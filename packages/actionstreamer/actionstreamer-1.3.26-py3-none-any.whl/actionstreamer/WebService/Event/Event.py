import json

from actionstreamer import CommonFunctions
from actionstreamer.Model import WebServiceResult
import actionstreamer.Config

def get_pending_event_list(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "POST"
        path = 'v1/event/list/pending'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceName": device_serial
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
        ws_result.description = str(ex)

    return ws_result 


def dequeue_event(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, agent_type: str) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "POST"
        path = 'v1/event/dequeue'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "agentType": agent_type
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
        ws_result.description = str(ex)

    return ws_result 


def create_event(ws_config: actionstreamer.Config.WebServiceConfig, device_id: int, device_serial: str, agent_type: str, event_type: str, server_event: int = 0, event_parameters: str = '', priority=1, max_attempts: int = 0, expiration_epoch: int = 0) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "POST"
        path = 'v1/event'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceID": device_id,
            "deviceSerial": device_serial,
            "agentType": agent_type,
            "eventType": event_type,
            "serverEvent": server_event,
            "eventParameters": event_parameters,
            "priority": priority,
            "maxAttempts": max_attempts,
            "expirationEpoch": expiration_epoch
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
        ws_result.description = str(ex)

    return ws_result


def get_event_details(ws_config: actionstreamer.Config.WebServiceConfig, event_id: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "GET"
        path = 'v1/event/' + str(event_id)
        url = ws_config.base_url + path
        parameters = ''
        headers = {}
        body = ''
        
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except json.JSONDecodeError:
        # Ignore JSON decode errors from the line above.
        pass
    except Exception as ex:
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result 


def update_event_progress(ws_config: actionstreamer.Config.WebServiceConfig, event_id: int, device_serial: str, percent_complete: float) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "PATCH"
        path = 'v1/event/' + str(event_id) + '/progress'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceName": device_serial,
            "deviceSerial": device_serial,
            "percentComplete": percent_complete
        }

        body = json.dumps(json_post_data)
        
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string

        if response_string:
            if not response_string == '':
                ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def update_event(ws_config: actionstreamer.Config.WebServiceConfig, event_id: int, event_status: int, result: str, process_id: int, tag_string: str ='', tag_number: int = 0, attempt_number: int = 1) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "PUT"
        path = 'v1/event/' + str(event_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "eventStatus": event_status,
            "attemptNumber": attempt_number,
            "result": result,
            "processID": process_id,
            "tagString": tag_string,
            "tagNumber": tag_number
        }

        body = json.dumps(json_post_data)
        
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string

        if response_string:
            if not response_string == '':
                ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def update_event_with_progress(ws_config: actionstreamer.Config.WebServiceConfig, event_id: int, event_status: int, result: str, process_id: int, tag_string: str ='', tag_number: int = 0, percent_complete: float = 0, attempt_number: int = 1) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "PUT"
        path = 'v1/event/' + str(event_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "eventStatus": event_status,
            "attemptNumber": attempt_number,
            "result": result,
            "processID": process_id,
            "percentComplete": percent_complete,
            "tagString": tag_string,
            "tagNumber": tag_number
        }

        body = json.dumps(json_post_data)
        
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)
        
        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string

        if response_string:
            if not response_string == '':
                ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result