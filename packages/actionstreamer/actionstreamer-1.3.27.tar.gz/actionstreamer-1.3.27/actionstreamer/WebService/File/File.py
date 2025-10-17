import json

from actionstreamer import CommonFunctions
from actionstreamer.Model import WebServiceResult
import actionstreamer.Config

def create_file(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, filename: str, file_size: int, sha256_hash: str) -> tuple[int, str, str, int]:

    """
    Create a file.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    device_serial (string): The device name.
    filename (string): The filename (no path information, just the name).
    file_size (int): The file size in bytes.
    sha256_hash (string): The SHA256 hash for the file.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    signed_url: The URL to upload the file to.
    file_id: The ID for the newly generated file.
    """

    try:
        json_post_data = {"deviceName":device_serial, "filename":filename, "fileSize":file_size, "sHA256Hash":sha256_hash, "deviceSerial":device_serial}

        method = "POST"
        path = 'v1/file'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = json.dumps(json_post_data)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        signed_url = ''
        file_id = 0
        
        if (response_code == 200):

            # This response should include signedURL, fileID
            response_data = json.loads(response_string)

            signed_url = response_data['signedURL']
            file_id = response_data['fileID']

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in create_file"
        signed_url = ""
        file_id = 0

    return response_code, response_string, signed_url, file_id


def create_temp_file(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, filename: str, file_size: int, sha256_hash: str) -> tuple[int, str, str, int]:

    """
    Create a temp file.  This file will be deleted from S3 after 24 hours.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    device_serial (string): The device serial number.
    filename (string): The filename (no path information, just the name).
    file_size (int): The file size in bytes.
    sha256_hash (string): The SHA256 hash for the file.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    signed_url: The URL to upload the file to.
    file_id: The ID for the newly generated file.
    """

    try:
        json_post_data = {"deviceName":device_serial, "filename":filename, "fileSize":file_size, "sHA256Hash":sha256_hash, "deviceSerial":device_serial}

        method = "POST"
        path = 'v1/file/temp'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = json.dumps(json_post_data)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        signed_url = ''
        file_id = 0
        
        if (response_code == 200):

            # This response should include signedURL, fileID
            response_data = json.loads(response_string)

            signed_url = response_data['signedURL']
            file_id = response_data['fileID']

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in create_file"
        signed_url = ""
        file_id = 0

    return response_code, response_string, signed_url, file_id


def update_file_upload_success(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, file_id: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        json_post_data = {'deviceSerial':device_serial}

        method = "POST"
        path = 'v1/file/success/' + str(file_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = json.dumps(json_post_data)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in update_file_upload_success"

    return ws_result


def get_file(ws_config: actionstreamer.Config.WebServiceConfig, file_id: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "GET"
        path = 'v1/file/' + str(file_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_file at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result