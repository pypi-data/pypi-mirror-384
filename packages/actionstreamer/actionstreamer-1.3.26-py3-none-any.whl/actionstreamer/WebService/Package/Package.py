import json

from actionstreamer import CommonFunctions
from actionstreamer.Model import WebServiceResult
import actionstreamer.Config

def get_package(ws_config: actionstreamer.Config.WebServiceConfig, package_id: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "GET"
        path = 'v1/package/' + str(package_id)
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


def get_package_list(ws_config: actionstreamer.Config.WebServiceConfig) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "POST"
        path = 'v1/package/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        body = {}

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in get_video_clip_list at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result