import getopt
import json
import socket
import sys
import platform
import subprocess
from actionstreamer import CommonFunctions
from actionstreamer.Model import WebServiceResult
import actionstreamer.Config

def process_cpuinfo() -> str:

    device_serial = "0000000000000000"

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'm:')

    except getopt.GetoptError as err:
        # Print help information and exit:
        print(str(err))    # This will print something like "option -a not recognized"
        return device_serial

    for option, argument in optlist:
        if option == "-m":
            device_serial = argument

    return device_serial


def get_serial_number() -> str:
    try:
        serial_number = ""
    
        if platform.system() == "Windows":
            serial_number = get_cpu_serial_number_windows()
        
        elif platform.system() == "Linux":
            serial_number =  get_cpu_serial_number_linux()
        
        else:
            serial_number = ""

        return serial_number
    
    except:
        return "serial_error"


def get_ip_address() -> str:

    try:
        # Get the local hostname
        hostname = socket.gethostname()
        # Get the IP address associated with the hostname
        ip_address = socket.gethostbyname(hostname)
    except socket.error:
        # If an error occurs, return a default IP address
        ip_address = "0.0.0.0"
            
    return ip_address


def get_cpu_serial_number_windows() -> str:

    try:
        import wmi
        wmi_object = wmi.WMI()
        for processor in wmi_object.Win32_Processor():
            return processor.ProcessorId.strip()
        
    except Exception as ex:
        return str(ex)


def get_cpu_serial_number_linux() -> str:

    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.strip().startswith("Serial"):
                    return line.strip().split(":")[1].strip()
                
    except Exception as ex:
        return str(ex)
    

def get_manufacturer() -> tuple[str, int]:

    if platform.system() == "Windows":
        return get_manufacturer_windows()
    else:
        return get_manufacturer_linux()


def get_manufacturer_windows() -> tuple[str, int]:
    try:
        import wmi
        w = wmi.WMI()
        for processor in w.Win32_Processor():
            return parse_manufacturer(processor.Manufacturer.strip()), 0
    except Exception as e:
        print(f"Exception in get_manufacturer_windows: {e}")
        return "", 1

    return "", 1


def get_manufacturer_linux() -> tuple[str, int]:
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Model"):
                    model = line.split(":")[1].strip()
                    if "Raspberry Pi" in model:
                        return parse_raspberry_pi_model(model), 0
        # Fall back to using dmidecode if not a Raspberry Pi
        result = subprocess.run(['dmidecode', '-t', 'processor'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in result.stdout.splitlines():
            if line.strip().startswith("Manufacturer"):
                return parse_manufacturer(line.split(":")[1].strip()), 0
    except Exception as e:
        print(f"Exception in get_manufacturer_linux: {e}")
        return "", 1

    return "", 1


def parse_raspberry_pi_model(model: str) -> str:
    
    if "Raspberry Pi" in model:
        parts = model.split()
        if len(parts) >= 3 and parts[2].isdigit():
            return f"RPi{parts[2]}"
    return model


def parse_manufacturer(manufacturer: str) -> str:

    if "Intel" in manufacturer:
        return "Intel"
    elif "AMD" in manufacturer:
        return "AMD"
    elif "Broadcom" in manufacturer:
        return "Broadcom"
    elif "ARM" in manufacturer:
        return "ARM"
    else:
        return manufacturer
