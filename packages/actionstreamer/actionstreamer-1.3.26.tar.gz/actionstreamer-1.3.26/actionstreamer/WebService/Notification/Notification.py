import json
import urllib
from typing import List
from actionstreamer import CommonFunctions
import actionstreamer.Config
from actionstreamer.Model import WebServiceResult


def get_notification_list(ws_config: actionstreamer.Config.WebServiceConfig, last_epoch_time: int, seen_in_app: bool = False, sent_as_email: bool = False) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "GET"
        path = 'v1/notification/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
                
        parameters = {
            "last_epoch_time": str(last_epoch_time),
            "seen_in_app": str(seen_in_app).lower(),
            "sent_as_email": str(sent_as_email).lower()
        }
        
        body = '' #json.dumps(json_post_data)

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