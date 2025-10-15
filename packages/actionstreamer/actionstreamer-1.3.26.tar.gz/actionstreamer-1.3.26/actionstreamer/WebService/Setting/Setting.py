import json

import actionstreamer.CommonFunctions
import actionstreamer.Config
from actionstreamer.Model import WebServiceResult


def get_device_setting(ws_config: actionstreamer.Config.WebServiceConfig, device_id: int, setting_name: str) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "GET"
        path = f"v1/devicesetting/device/{device_id}"
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = {"setting_name": setting_name} 
        
        body = ""

        response_code, response_string = actionstreamer.CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = actionstreamer.CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def update_device_setting(ws_config: actionstreamer.Config.WebServiceConfig, device_id: int, setting_name: str, setting_value: str) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "PUT"
        path = f"v1/devicesetting/device/{device_id}"
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        
        json_post_data = {"name":setting_name, "value":setting_value}

        body = json.dumps(json_post_data)

        response_code, response_string = actionstreamer.CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = actionstreamer.CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_device at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result