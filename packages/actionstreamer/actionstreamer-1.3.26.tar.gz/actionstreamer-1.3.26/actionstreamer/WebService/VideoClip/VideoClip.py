import json
import urllib
from typing import List
from actionstreamer import CommonFunctions
import actionstreamer.Config
from actionstreamer.Model import WebServiceResult
from actionstreamer.WebService import Patch
from actionstreamer.Model import CreateVideoClip
from actionstreamer.Model import VideoClip

def create_video_clip(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, create_video_clip: CreateVideoClip) -> tuple[int, str]:

    try:
        device_serial = device_serial.replace(" ", "")
        device_serial = urllib.parse.quote(device_serial)

        method = "POST"
        path = 'v1/videoclip/' + device_serial
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = json.dumps(create_video_clip.to_dict())

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in CreateVideoClip. Line number " + str(line_number)

    return response_code, response_string


def delete_video_clip(ws_config: actionstreamer.Config.WebServiceConfig, video_clip_id: int) -> tuple[int, str]:

    """
    Delete a video clip.  This also deletes the associated file in the cloud if it has been uploaded.
    
    Parameters:
    ws_config (Config.WebServiceConfig): The web service configuration.
    video_clip_id (int): The FileID.
    
    Returns:
    response_code: The API HTTP response code.
    response_string: The API HTTP response body
    """

    try:
        method = "DELETE"
        path = f'v1/videoclip/{video_clip_id}'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = ''

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()

        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in create_file"

    return response_code, response_string


def create_video_clip_list(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, video_clips: List[VideoClip]) -> tuple[int, str]:

    try:
        # Clean and encode device_serial
        device_serial = device_serial.replace(" ", "")
        device_serial = urllib.parse.quote(device_serial)

        method = "POST"
        path = 'v1/videoclip/createlist/' + device_serial
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        
        # Convert the list of CreateVideoClip objects to a list of dictionaries for JSON serialization
        clips_data = [clip.to_dict() for clip in video_clips]
        body = json.dumps(clips_data)

        # Send the request to the API
        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in CreateVideoClipList. Line number " + str(line_number)

    return response_code, response_string


def update_file_id(ws_config: actionstreamer.Config.WebServiceConfig, video_clip_id: int, file_id: int) -> tuple[int, str]:

    try:
        operations_list = []
        Patch.add_patch_operation(operations_list, "FileID", file_id)

        method = "PATCH"
        path = 'v1/videoclip/' + str(video_clip_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = Patch.generate_patch_json(operations_list)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in UpdateVideoClipFileID Line number " + str(line_number)

    return response_code, response_string


def get_video_clip(ws_config: actionstreamer.Config.WebServiceConfig, video_clip_id: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "GET"
        path = 'v1/videoclip/' + str(video_clip_id)
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
            print(f"Exception occurred in get_video_clip at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def update_status(ws_config: actionstreamer.Config.WebServiceConfig, video_clip_id: int, status: int) -> tuple[int, str]:

    try:
        operations_list = []
        Patch.add_patch_operation(operations_list, "VideoClipStatus", status)

        method = "PATCH"
        path = 'v1/videoclip/' + str(video_clip_id)
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = Patch.generate_patch_json(operations_list)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in VideoClip.update_status, line number " + str(line_number)

    return response_code, response_string


def get_video_clip_list(ws_config: actionstreamer.Config.WebServiceConfig, device_id: int, start_epoch: int, end_epoch: int, count: int = 0, order: str = 'desc', video_clip_type_id = 1) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "POST"
        path = 'v1/videoclip/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        
        json_post_data = {
            "deviceID": device_id,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch,
            "count": count,
            "order": order,
            "videoClipTypeID": video_clip_type_id
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
            print(f"Exception occurred in get_video_clip_list at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def get_extract_video_clip_list(ws_config: actionstreamer.Config.WebServiceConfig, serial_number: str, start_epoch: int, end_epoch: int) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "POST"
        path = 'v1/videoclip/extract/list'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        
        json_post_data = {
            "deviceSerial": serial_number,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch
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
            print(f"Exception occurred in get_extract_video_clip_list at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result


def concatenate_clips(ws_config: actionstreamer.Config.WebServiceConfig, device_id: int, device_name: str, start_epoch: int, end_epoch: int, upload_url: str, postback_url: str, use_vrs: bool = False, timeout: int = 0) -> WebServiceResult:

    ws_result = WebServiceResult(0, '', '', '', None)

    try:

        method = "POST"
        path = 'v1/videoclip/concatenate'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        query_params = ''

        if use_vrs:
            status = 'True'
        else:
            status = 'False'

        query_params: Dict[str, str] = {
            "usevrs": status
        }

        json_post_data = {
            "deviceID": device_id,
            "deviceName": device_name,
            "startEpoch": start_epoch,
            "endEpoch": end_epoch,
            "uploadURL": upload_url,
            "postbackURL": postback_url,
            "timeout": timeout
        }

        body = json.dumps(json_post_data)

        response_code, response_string = CommonFunctions.send_signed_request(ws_config, method, url, path, headers, query_params, body)

        ws_result.http_response_code = response_code
        ws_result.http_response_string = response_string
        ws_result.json_data = json.loads(response_string)

    except Exception as ex:
        
        ws_result.code = -1
        filename, line_number = CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred in concatenate_clips at line {line_number} in {filename}")
        print(ex)
        ws_result.description = str(ex)

    return ws_result