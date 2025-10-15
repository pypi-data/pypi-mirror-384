import json

import actionstreamer.CommonFunctions
import actionstreamer.Config


def register_agent(ws_config: actionstreamer.Config.WebServiceConfig, device_serial: str, agent_type: str, agent_version: str, agent_index: int, process_id: int) -> tuple[int, str]:

    try:        
        json_post_data = {"deviceName":device_serial, "agentType":agent_type, "agentVersion":agent_version, "agentIndex":agent_index, "processID":process_id}

        method = "POST"
        path = 'v1/agent'
        url = ws_config.base_url + path
        headers = {"Content-Type": "application/json"}
        parameters = ''
        body = json.dumps(json_post_data)
        
        response_code, response_string = actionstreamer.CommonFunctions.send_signed_request(ws_config, method, url, path, headers, parameters, body)

    except Exception as ex:
        
        filename, line_number = actionstreamer.CommonFunctions.get_exception_info()
        if filename is not None and line_number is not None:
            print(f"Exception occurred at line {line_number} in {filename}")
        print(ex)

        response_code = -1
        response_string = "Exception in RegisterAgent"

    return response_code, response_string
