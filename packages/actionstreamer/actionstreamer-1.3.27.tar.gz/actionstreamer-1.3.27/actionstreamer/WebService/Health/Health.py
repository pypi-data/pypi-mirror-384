import json

from actionstreamer import CommonFunctions
from actionstreamer.Model import WebServiceResult
import actionstreamer.Config


def create_health(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, health_json: str) -> WebServiceResult:
    
    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "POST"
        path = 'v1/devicehealth'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "healthJSON": health_json
        }

        body = json.dumps(json_post_data)
        
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

    return ws_result


def update_health(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, health_json: str) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "POST"
        path = 'v1/devicehealth/updatelatest'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "healthJSON": health_json
        }

        body = json.dumps(json_post_data)
        
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

    return ws_result


def get_health_list(ws_config: actionstreamer.Config.WebServiceConfig, device_id: int, start_epoch: int, end_epoch: int, count: int = 0, order: str = 'desc') -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "POST"
        path = 'v1/devicehealth/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        
        json_post_data = {
            "deviceID": device_id,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch,
            "count": count,
            "order": order
        }

        body = json.dumps(json_post_data)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_health_list at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def get_device_health_rows(ws_config: actionstreamer.Config.WebServiceConfig, online_only: bool = True) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        if online_only:
            status = 'online'
        else:
            status = 'all'

        query_params: Dict[str, str] = {
            "status": status
        }

        method = "POST"
        path = 'v1/device/list/health'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        
        body = ''

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, query_params, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_health_list at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result