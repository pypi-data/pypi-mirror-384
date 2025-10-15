import json

from actionstreamer import CommonFunctions, Model
from actionstreamer.Model import WebServiceResult
import actionstreamer.Config

def run_event_preset(ws_config: actionstreamer.Config.WebServiceConfig, event_preset_id: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:
        method = "POST"
        path = 'v1/eventpreset/run/' + str(event_preset_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {}
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


def create_event_preset(ws_config: actionstreamer.Config.WebServiceConfig, event_preset: Model.EventPreset, event_type: Model.EventType, event_parameters: Model.RecordingArgs | Model.RTMPArgs | Model.ConferenceArgs) -> tuple[int, str]:

    try:
        method = "POST"
        path = 'v1/eventpreset/'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        # Set the event parameters based on the event type.
        if event_type == Model.EventType.Video.Start_recording:
           event_parameters_json = event_parameters.to_json()

        elif event_type == Model.EventType.Video.Stop_recording:
            event_parameters_json = None

        elif event_type == Model.EventType.Video.Start_RTMP:
            event_parameters_json = event_parameters.to_json()

        elif event_type == Model.EventType.Video.Stop_RTMP:
            event_parameters_json = None

        elif event_type == Model.EventType.Video.Join_conference:
            event_parameters_json = event_parameters.to_json()

        elif event_type == Model.EventType.Video.Leave_conference:
            event_parameters_json = None

        else:
            raise ValueError('Invalid event type')

        event_preset.eventParameters = event_parameters_json

        body = json.dumps(event_preset.__dict__)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in create_event_preset. Line number " + str(line_number)

    return response_code, response_string


def set_startup_preset(ws_config: actionstreamer.Config.WebServiceConfig, event_preset_id: int, offline_preset: bool = False, device_id: int = 0, device_group_id: int = 0) -> tuple[int, str]:

    # If device_group_id is set, device_id will be ignored.

    try:
        if offline_preset == True:
            device_state = 'online'
        else:
            device_state = 'offline'

        method = "POST"
        path = f'v1/eventpreset/startupevent/{device_state}/{event_preset_id}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''

        json_post_data = {
            "deviceID": device_id,
            "deviceGroupID": device_group_id
        }

        body = json.dumps(json_post_data)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in create_event_preset. Line number " + str(line_number)

    return response_code, response_string

