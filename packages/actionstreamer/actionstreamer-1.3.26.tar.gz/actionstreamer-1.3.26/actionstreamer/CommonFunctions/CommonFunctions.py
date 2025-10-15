import json
import sys
import hashlib
import hmac
import uuid
import subprocess
import time
import zipfile
from datetime import datetime, timezone
import requests
import os
import re
import glob
from typing import NamedTuple
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
import pytz
import requests
import getpass

import actionstreamer.Config

class StandardResult:

    def __init__(self, code: int, description: str):
        self.Code = code
        self.Description = description
        

class switch(object):

	def __init__(self, value):
		self.value = value
		self.fall = False

	def __iter__(self):
		"""Return the match method once, then stop"""
		yield self.match
		raise StopIteration
    
	def match(self, *args) -> bool:
		"""Indicate whether or not to enter a case suite"""
		if self.fall or not args:
			return True
		elif self.value in args:
			self.fall = True
			return True
		else:
			return False


class FileInfo(NamedTuple):
    file_path: str
    creation_time: float
    file_size: int


def get_creation_time(file_info: FileInfo) -> float:
    return file_info.creation_time


def get_exception_info() -> tuple[str, int] | tuple[None, None]:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    if exception_traceback is not None:
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        return filename, line_number
    return None, None


def get_line_number() -> int | None:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    if exception_traceback is not None:
        return exception_traceback.tb_lineno
    return None


def log_to_console(message: str, agent_name: str = '') -> None:
    # Get the current UTC time
    utc_now = datetime.now(pytz.utc)
    
    # Format the UTC time
    utc_time_formatted = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Prepend the formatted UTC time to the string
    if (agent_name):
        result_string = f"[{utc_time_formatted}]: [{agent_name}]: {message}"
    else:
        result_string = f"[{utc_time_formatted}]: {message}"
    
    # Print the result to standard output
    print(result_string)
    sys.stdout.flush()


def send_signed_request(ws_config: actionstreamer.Config.WebServiceConfig, method: str, url: str, path: str, headers: Dict[str, str] = None, parameters: Dict[str, str] = None, body: str = None) -> tuple[int, str]:
    
    try:
        if headers is None:
            headers = {"Content-Type": "application/json"}
        elif isinstance(headers, str):
            headers = dict(header.strip().split(':', 1) for header in headers.split('\n'))

        nonce = str(uuid.uuid4())
        timestamp = str(int(time.time()))

        headers['X-Nonce'] = nonce
        headers['X-Timestamp'] = timestamp
        headers['Authorization'] = 'HMAC-SHA256 ' + ws_config.access_key
        headers['X-AccessKey'] = ws_config.access_key

        # Generate HMAC signature
        signature, string_to_sign = get_hmac_signature(ws_config.secret_key, method, path, headers, parameters, body)

        # Include signature in headers
        headers['X-Signature'] = signature

        verify = not ws_config.ignore_ssl
        
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=body, params=parameters, verify=verify, timeout=ws_config.timeout)
        elif method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=parameters, verify=verify, timeout=ws_config.timeout)
        if method.upper() == 'PUT':
            response = requests.put(url, headers=headers, data=body, params=parameters, verify=verify, timeout=ws_config.timeout)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, headers=headers, data=body, params=parameters, verify=verify, timeout=ws_config.timeout)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, params=parameters, verify=verify, timeout=ws_config.timeout)

        status_code = response.status_code
        response_string = response.content.decode('utf-8')

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        status_code = -1
        response_string = "Error in send_signed_request"

    return status_code, response_string
   

def get_hmac_signature(secret_key: str, method: str, path: str, headers: Dict[str, str] = None, parameters: Dict[str, str] = None, body: str = None)-> tuple[str, str] | None:
    
    try:
        if 'Content-Type' in headers:
            del headers['Content-Type']

        header_string = dictionary_to_string(headers)
        parameter_string = dictionary_to_string(parameters)

        # Path should be in the format /v1/event
        if not path.startswith('/'):
            path = '/' + path

        if path.endswith('/') and len(path) > 1:
            path = path[:-1]

        string_to_sign = '\n'.join([method, path, header_string, parameter_string, body if body else ''])

        string_to_sign = string_to_sign.strip()
        #log_to_console("stringToSign: " + string_to_sign)
        
        # Generate the HMAC SHA256 signature
        hmac_signature = hmac.new(secret_key.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256)

        # Convert the HMAC signature to hexadecimal
        return hmac_signature.hexdigest(), string_to_sign

    except Exception as ex:
        filename, line_number = get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)


def dictionary_to_string(dictionary: dict) -> str:

    result = ''

    try:
        sorted_keys = sorted(dictionary.keys())
        
        for key in sorted_keys:
            result += f"{key}: {dictionary[key]}\n"
        
    except Exception as ex:
        filename, line_number = get_exception_info()
        #if filename is not None and line_number is not None:
            #print(f"Exception occurred at line {line_number} in {filename}")
        #print(ex)
    
    return result


def upload_file_to_s3(file_path: str, signed_url: str, timeout: int = 0) -> int:

    retry = True
    retry_count = 0
    result = 0

    while retry:

        try:
            retry_count += 1

            if retry_count > 5:
                retry = False
                result = -3
                print("Retry limit exceeded")
                break

            with open(file_path, 'rb') as file:
                response = requests.put(signed_url, data=file, timeout=timeout)

            if response.status_code == 200:
                retry = False
                result = 0
            else:
                print(f"Error uploading file to S3. Status code: {response.status_code}")
                result = -1
                time.sleep(1)

        except requests.exceptions.Timeout:
            print("Upload timed out")
            result = -4
            time.sleep(1)

        except Exception as ex:
            print("Exception occurred while uploading file to S3:", str(ex))
            result = -2
            time.sleep(1)

    return result


def download_file(file_path: str, url: str) -> int:

    retry = True
    result = 0
    retry_count = 0
    
    while retry:

        try:
            retry_count = retry_count + 1

            if retry_count > 5:
                retry = False
                result = -3
                print("Retry limit exceeded")

            with requests.get(url, stream=True) as response:
                response.raise_for_status()  # Check for any errors

                # Open a local file for writing in binary mode
                with open(file_path, 'wb') as file:
                    # Write the content to the local file in chunks
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            
            retry = False

        except Exception as ex:
            print("Exception occurred while downloading file:", str(ex))
            result = -2
        
    return result


def get_sha256_hash_for_file(file_path: str) -> str:
    # Initialize the hash object (SHA-256 is used in this example)
    hash_object = hashlib.sha256()

    # Open the file in binary mode to read its contents
    with open(file_path, "rb") as file:
        # Read the file in chunks to avoid loading the entire file into memory
        for chunk in iter(lambda: file.read(4096), b""):
            hash_object.update(chunk)

    # Get the hexadecimal representation of the hash
    file_hash = hash_object.hexdigest()
    
    return file_hash


def create_folders(path: str) -> None:
    # Split the path into individual folders
    folders = path.split(os.sep)

    # Initialize the base folder to the root of the file system
    base_folder = ""

    # Loop through each folder in the path
    for folder in folders:
        # Append the current folder to the base folder
        base_folder = os.path.join(base_folder, folder)

        # Check if the current folder exists
        if not os.path.exists(base_folder):
            # If not, create the folder
            os.makedirs(base_folder)


def get_cpu_frequency() -> float:
    with open("/proc/cpuinfo") as f:
        cpuinfo = f.read()
    # Find the first occurrence of "cpu MHz"
    match = re.search(r"cpu MHz\s+:\s+(\d+\.\d+)", cpuinfo)
    if match:
        return float(match.group(1))
    else:
        raise RuntimeError("Unable to find CPU frequency in /proc/cpuinfo")


def get_clock_cycles_per_millisecond() -> float:

    frequency_mhz = get_cpu_frequency()
    frequency_hz = frequency_mhz * 1_000_000
    cycles_per_millisecond = frequency_hz / 1_000

    return cycles_per_millisecond


def concatenate_videos(input_file_path1: str, input_file_path2: str, output_file_path: str):

    # Generate a unique file name for the temporary file list
    temp_file_name = str(uuid.uuid4()) + '.txt'
    temp_file_path = os.path.join('/tmp', temp_file_name)

    with open(temp_file_path, 'w') as filelist:
        filelist.write(f"file '{input_file_path1}'\n")
        filelist.write(f"file '{input_file_path2}'\n")
    
    # Run the ffmpeg command to concatenate the videos
    try:
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', temp_file_path, '-c', 'copy', '-y', output_file_path], check=True)
    except subprocess.CalledProcessError as ex:
        print(f"Error occurred: {ex}")
    finally:
        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except OSError as e:
            print(f"Error removing temporary file: {e}")


def concatenate_videos_by_list(list_file_path: str, output_file_path: str):
    
    # Run the ffmpeg command to concatenate the videos
    try:
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', '-y', output_file_path], check=True)
        
    except subprocess.CalledProcessError as ex:
        print(f"An error occurred: {ex}")
        

def concatenate_videos_by_list2(list_file_path: str, output_file_path: str):
    
    # Run the ffmpeg command to concatenate the videos
    try:
        command = "cpulimit -l 50 -- ffmpeg -f concat -safe 0 -i " + list_file_path + " -c copy -y " + output_file_path
        #subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', '-y', output_file_path], check=True)
        subprocess.run(command, shell=True)
    except subprocess.CalledProcessError as ex:
        print(f"An error occurred: {ex}")


def get_video_length_in_seconds(file_path: str):

    """Get the length of a video in seconds."""
    result = subprocess.run(['ffmpeg', '-i', file_path], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    output = result.stderr

    # Find the duration in the output
    duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', output)
    
    if not duration_match:
        raise ValueError(f"Could not determine the duration of the video {file_path}")

    hours, minutes, seconds = map(float, duration_match.groups())
    total_seconds = hours * 3600 + minutes * 60 + seconds
    total_seconds = total_seconds

    return total_seconds


def change_hostname(new_hostname: str):

    try:
        # Validate the new hostname
        if not new_hostname.isalnum() or len(new_hostname) > 63:
            raise ValueError("Hostname must be alphanumeric and no more than 63 characters long.")

        # Update /etc/hostname
        with open('/etc/hostname', 'w') as hostname_file:
            hostname_file.write(new_hostname + '\n')

        # Update /etc/hosts
        with open('/etc/hosts', 'r') as hosts_file:
            hosts_content = hosts_file.readlines()

        with open('/etc/hosts', 'w') as hosts_file:
            for line in hosts_content:
                if '127.0.1.1' in line:
                    hosts_file.write(f'127.0.1.1\t{new_hostname}\n')
                else:
                    hosts_file.write(line)

        # Apply the hostname change immediately
        os.system(f'hostname {new_hostname}')

        print(f"Hostname changed to {new_hostname}. Please reboot the system for all changes to take effect.")

    except Exception as ex:
        print("Exception occurred while changing hostname:", str(ex))


def convert_to_epoch(date_string: str, is_already_utc: bool = False):

    epoch_time = 0

    try:
        # Define the date format that matches the input string
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # Parse the string into a datetime object
        dt = datetime.strptime(date_string, date_format)
        
        if is_already_utc:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert the datetime object to epoch time (Unix timestamp)
        epoch_time = int(dt.timestamp())
    
    except:
        pass

    return epoch_time


def delete_old_files_max_folder_size(folder_path: str, max_size_mb: int):
    max_size_bytes = max_size_mb * 1024 * 1024
    file_list = []

    # Collect file details
    for file_path in glob.glob(os.path.join(folder_path, "*")):
        if os.path.isfile(file_path):
            creation_time = os.path.getctime(file_path)
            file_size = os.path.getsize(file_path)
            file_list.append(FileInfo(file_path, creation_time, file_size))

    total_size = sum(file_info.file_size for file_info in file_list)

    if total_size <= max_size_bytes:
        return  # No need to delete anything

    # Sort files by creation time (oldest first)
    file_list.sort(key=get_creation_time)

    # Delete oldest files until within size limit
    for file_info in file_list:
        os.remove(file_info.file_path)
        total_size -= file_info.file_size

        if total_size <= max_size_bytes:
            break


def delete_old_files(folder_path: str, needed_bytes: int):

    try:
        # Get the list of files in the folder with their creation times
        file_list = []

        for filename in os.listdir(folder_path):

            file_path = os.path.join(folder_path, filename)

            if os.path.isfile(file_path):
                creation_time = os.path.getctime(file_path)
                file_size = os.path.getsize(file_path)
                file_list.append((file_path, creation_time, file_size))

        # Sort the files by creation time
        file_list.sort(key=lambda x: x[1])

        # Delete the oldest files until enough space is freed up
        for file_path, creation_time, file_size in file_list:
            if needed_bytes <= 0:
                break
            os.remove(file_path)
            needed_bytes -= file_size
    
        result = 0

    except:
        result = -1

    return result


def get_free_disk_space_in_bytes():

    try:
        # Get the disk information
        disk_info = os.statvfs("/")

        # Calculate the total space in GB
        # total_space = disk_info.f_blocks * disk_info.f_bsize / (1024.0 * 1024.0 * 1024.0)

        # Calculate the available space in GB
        available_space_bytes = disk_info.f_bavail * disk_info.f_bsize

        #print(f"Total space: {total_space} GB")
        #print(f"Available space: {available_space_bytes} GB")
        return available_space_bytes
    
    except:
        return -1
    

def delete_until_space_freed(delete_from_folder_path: str, needed_bytes: int):

    try:
        while True:
            # Get the number of files
            num_files = len(os.listdir(delete_from_folder_path))

            # If there are less than 10 files, break the loop
            if num_files < 10:
                break

            # Get the available space
            available_space_bytes = os.statvfs("/").f_bavail * os.statvfs("/").f_bsize

            # If the available space is greater than the needed space, stop the loop
            if available_space_bytes > needed_bytes:
                break
            else:
                bytes_to_delete = needed_bytes - available_space_bytes

            # Delete files
            delete_old_files(delete_from_folder_path, bytes_to_delete)
            time.sleep(1)

        return 0

    except:
        return -1
    
    
def trim_mp4_beginning(file_path: str, seconds_to_trim: int, new_file_path: str):
    # Calculate the start time for the trimmed video
    start = int(seconds_to_trim * 1000)

    try:
        # Define the ffmpeg command
        command = f"ffmpeg -ss {start} -i '{file_path}' -c copy '{new_file_path}'"

        # Execute the ffmpeg command
        subprocess.run(command, shell=True)

        print(f"Trimmed {seconds_to_trim} seconds from {file_path} and saved as {new_file_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return -1
    

def trim_mp4_end(file_path: str, clip_length_in_s: int, seconds_to_trim: int, new_file_path: str):
    # Calculate the duration of the video in milliseconds
    duration = int(clip_length_in_s * 1000)

    # Calculate the end time for the trimmed video
    end = duration - (int(seconds_to_trim * 1000))

    # Define the ffmpeg command
    command = f"ffmpeg -i '{file_path}' -t {end} -c copy '{new_file_path}'"

    try:
        # Execute the ffmpeg command
        subprocess.run(command, shell=True)

        print(f"Trimmed {seconds_to_trim} seconds from the end of {file_path} and saved as {new_file_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return -1
    

def capture_dmesg(output_folder_path: str, delete_old_logs: bool = False):
    try:
        # Ensure the output folder exists
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        # Get the current date and time formatted as 'YYYY-MM-DD_HH-MM-SS'
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Define the output file path with the timestamp in the filename
        output_file = os.path.join(output_folder_path, f'dmesg_{timestamp}.log')

        # Run the 'dmesg' command and capture the output
        dmesg_output = subprocess.check_output(['dmesg'], text=True)

        # Save the output to the file
        with open(output_file, 'w') as file:
            file.write(dmesg_output)

        print(f"dmesg output saved to {output_file}")

        # If delete_old_logs is True, remove older log files, keeping only the most recent 20
        if delete_old_logs:
            manage_old_files(output_folder_path)

    except Exception as e:
        print(f"Error capturing dmesg: {e}")


def manage_old_files(folder_path: str, files_to_keep: int = 20, file_extension: str = '.log'):
    try:
        # List all .log files in the output folder, sorted by modification time
        log_files = [f for f in os.listdir(folder_path) if f.endswith(file_extension)]
        log_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))

        # If there are more than files_to_keep log files, delete the oldest ones
        if len(log_files) > files_to_keep:
            for old_log in log_files[:-files_to_keep]:  # Keep the most recent 20 logs
                os.remove(os.path.join(folder_path, old_log))
                print(f"Deleted old file: {old_log}")

    except Exception as e:
        print(f"Error managing old files: {e}")


def safe_delete(file_path: str, retries: int = 5, delay: int = 1):
    for attempt in range(retries):
        try:
            os.remove(file_path)
            print(f"File {file_path} deleted successfully.")
            return
        except OSError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    print(f"Failed to delete {file_path} after {retries} attempts.")


def delete_file_async(file_path: str):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(safe_delete, file_path)
    return future


def encrypt_file_gpg_aes256(input_file_path: str, password: str) -> str:
    """
    Encrypts a file using GPG with AES-256 encryption on Windows and Linux.

    Args:
        input_file_path (str): Full path to the file to encrypt.
        password (str): Password for encryption.

    Returns:
        str: Full path to the encrypted file.
    """
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    encrypted_file_path = f"{input_file_path}.gpg"

    # Construct the GPG command
    cmd = [
        "gpg", "--batch", "--yes", "--passphrase", password,
        "-c", "--cipher-algo", "AES256", input_file_path
    ]

    try:
        # Run GPG process securely
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"GPG encryption failed: {e.stderr.decode()}")

    if not os.path.isfile(encrypted_file_path):
        raise RuntimeError("Encryption failed: Output file not created.")

    return encrypted_file_path


def decrypt_file_gpg_aes256(encrypted_file_path: str, password: str) -> str:
    """
    Decrypts a GPG-encrypted file using AES-256 on Windows and Linux.

    Args:
        encrypted_file_path (str): Full path to the encrypted `.gpg` file.
        password (str): Password for decryption.

    Returns:
        str: Full path to the decrypted file.
    """
    if not os.path.isfile(encrypted_file_path):
        raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")

    decrypted_file_path = encrypted_file_path.rsplit(".gpg", 1)[0]  # Remove .gpg extension

    # Construct the GPG command
    cmd = [
        "gpg", "--batch", "--yes", "--passphrase", password,
        "--output", decrypted_file_path, "--decrypt", encrypted_file_path
    ]

    try:
        # Run GPG process securely
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"GPG decryption failed: {e.stderr.decode()}")

    if not os.path.isfile(decrypted_file_path):
        raise RuntimeError("Decryption failed: Output file not created.")

    return decrypted_file_path


def read_all_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    

def unzip_file(zip_file_path: str, output_folder_path: str):
    """
    Unzips a zip file to a specified folder.

    Args:
        zip_file_path (str): Path to the zip file.
        output_folder_path (str): Path to the folder where the contents will be extracted.

    Returns:
        None
    """
    # Check if the zip file exists
    if not os.path.isfile(zip_file_path):
        raise FileNotFoundError(f"The zip file does not exist: {zip_file_path}")
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder_path, exist_ok=True)

    # Extract the zip file contents
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(output_folder_path)


def unzip_and_execute(zip_file_path, unzip_to_folder_path):
    # This function assumes there is a file called install.json inside the outer zip file, along with a deploy script and the inner zip file.
    # Outer zip file package_1.2.3.zip:
    # install.json
    # deploy.sh
    # package.zip

    try:
        # Extract the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_to_folder_path)

        install_json_file_path = os.path.join(unzip_to_folder_path, 'install.json')

        try:
            with open(install_json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                install_script_filename = data.get("installScriptFilename")
                zip_filename = data.get("zipFilename")

            # Identify the .sh and .zip files
            script_file_path = os.path.join(unzip_to_folder_path, install_script_filename)
            package_file_path = os.path.join(unzip_to_folder_path, zip_filename)

            # Make the script executable
            os.chmod(script_file_path, 0o755)

            # Execute the script with the package file path as an argument
            subprocess.run(['sudo', script_file_path, package_file_path], check=True)

            try:
                os.remove(package_file_path)
            except:
                pass
            try:
                os.remove(script_file_path)
            except:
                pass

        except Exception as ex:
            filename, line_number = get_exception_info()
            if filename is not None and line_number is not None:
                print(f"Exception occurred at line {line_number} in {filename}")
            print(ex)
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return None, None


def get_login_user():
    try:
        # Try `logname` first
        return subprocess.check_output(["logname"], text=True).strip()
    except Exception:
        pass

    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user and sudo_user != "root":
        return sudo_user

    # Fall back to current effective user
    return getpass.getuser()


def write_string_to_file(file_path: str, text: str) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)


def append_string_to_file(file_path: str, text: str) -> None:
    # Open in append mode with line buffering
    with open(file_path, "a", encoding="utf-8", buffering=1) as file:
        file.write(text + "\n")
        file.flush()          # Flush Python buffer to OS
        os.fsync(file.fileno())  # Force OS to write to disk


def log_message(base_folder_path: str, log_name: str, message: str, rotate_on_start: bool = False, prepend_datetime: bool = False) -> None:

    os.makedirs(base_folder_path, exist_ok=True)
    log_file_path = os.path.join(base_folder_path, log_name + ".log")

    if rotate_on_start and os.path.exists(log_file_path):

        previous_folder_path = os.path.join(base_folder_path, "previous")
        os.makedirs(previous_folder_path, exist_ok=True)

        archived_log_file_path = os.path.join(previous_folder_path, log_name + ".log")
        shutil.copy2(log_file_path, archived_log_file_path)

        # Clear current log file
        open(log_file_path, "w", encoding="utf-8").close()

    if prepend_datetime:
        timestamp = datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")
        message = f"{timestamp} {message}"

    append_string_to_file(log_file_path, message)


# Global executor for all fire-and-forget tasks
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

def fire_and_forget(func, *args, **kwargs):
    """
    Schedule any function to run in the background and ignore its result.
    """
    _executor.submit(func, *args, **kwargs)

