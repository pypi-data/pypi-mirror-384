import datetime
import json

from actionstreamer import CommonFunctions
from actionstreamer.Config import LogConfig


def create_log_message(log_config: LogConfig, message: str, log_to_console=True) -> tuple[int, str]:

    try:
        if (log_to_console):
            agent_name = str(log_config.agent_type) + "Agent:" + str(log_config.agent_index) + "_" + str(log_config.agent_version)
            CommonFunctions.log_to_console(message, agent_name)

        utc_now = datetime.datetime.now(datetime.timezone.utc)
        post_data = {"deviceName": log_config.device_serial, "agentType": log_config.agent_type, "agentVersion": log_config.agent_version, "agentIndex": log_config.agent_index, "processID": log_config.process_id, "message": message, "logDate": str(utc_now), "deviceSerial": log_config.device_serial}

        method = "POST"
        path = 'v1/logmessage'
        url = log_config.ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = json.dumps(post_data)

        response_code, response_string = CommonFunctions.send_signed_request(log_config.ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in CreateLogMessage"

    return response_code, response_string