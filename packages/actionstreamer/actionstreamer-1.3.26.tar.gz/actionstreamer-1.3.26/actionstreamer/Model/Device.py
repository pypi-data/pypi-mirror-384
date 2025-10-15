import json
from datetime import datetime


class Device:

    def __init__(
        self,
        key: int = 0,
        device_type_id: int = 0,
        user_id: int = 0,
        device_name: str = '',
        serial_number: str = '',
        device_description: str = '',
        recent_output: str = '',
        camera_status: str = '',
        last_ip_address: str = '',
        tunnel_ip_address: str = '',
        last_heard_from_date: datetime = datetime.now(),
        software_date: datetime = datetime.now(),
        location: str = '',
        setup_status: int = 0,
        auto_send_files: int = 0,
        run_startup_event: int = 0,
        device_ready_event_preset_id: int = 0,
        standalone_event_preset_id: int = 0,
        log_health: int = 0,
        run_analytics: int = 0,
        audio_channel_name: str = '',
        volume: int = 0,
        comment_list_id: int = 0,
        is_archived: bool = False,
        guid: str = '',
        creation_date: datetime = datetime.now(),
        created_by: int = 0,
        last_modified_date: datetime = datetime.now(),
        last_modified_by: int = 0,
        **kwargs
    ):
        self.key = key
        self.device_type_id = device_type_id
        self.user_id = user_id
        self.device_name = device_name
        self.serial_number = serial_number
        self.device_description = device_description
        self.recent_output = recent_output
        self.camera_status = camera_status
        self.last_ip_address = last_ip_address
        self.tunnel_ip_address = tunnel_ip_address
        self.last_heard_from_date = last_heard_from_date
        self.software_date = software_date
        self.location = location
        self.setup_status = setup_status
        self.auto_send_files = auto_send_files
        self.run_startup_event = run_startup_event
        self.device_ready_event_preset_id = device_ready_event_preset_id
        self.standalone_event_preset_id = standalone_event_preset_id
        self.log_health = log_health
        self.run_analytics = run_analytics
        self.audio_channel_name = audio_channel_name
        self.volume = volume
        self.comment_list_id = comment_list_id
        self.is_archived = is_archived
        self.guid = guid
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "deviceTypeID": "device_type_id",
            "userID": "user_id",
            "deviceName": "device_name",
            "serialNumber": "serial_number",
            "deviceDescription": "device_description",
            "recentOutput": "recent_output",
            "cameraStatus": "camera_status",
            "lastIPAddress": "last_ip_address",
            "tunnelIPAddress": "tunnel_ip_address",
            "lastHeardFromDate": "last_heard_from_date",
            "softwareDate": "software_date",
            "setupStatus": "setup_status",
            "autoSendFiles": "auto_send_files",
            "runStartupEvent": "run_startup_event",
            "deviceReadyEventPresetID": "device_ready_event_preset_id",
            "standaloneEventPresetID": "standalone_event_preset_id",
            "logHealth": "log_health",
            "runAnalytics": "run_analytics",
            "audioChannelName": "audio_channel_name",
            "commentListID": "comment_list_id",
            "isArchived": "is_archived",
            "gUID": "guid",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.key,
            "deviceTypeID": self.device_type_id,
            "userID": self.user_id,
            "deviceName": self.device_name,
            "serialNumber": self.serial_number,
            "deviceDescription": self.device_description,
            "recentOutput": self.recent_output,
            "cameraStatus": self.camera_status,
            "lastIPAddress": self.last_ip_address,
            "tunnelIPAddress": self.tunnel_ip_address,
            "lastHeardFromDate": self.last_heard_from_date.isoformat(),
            "softwareDate": self.software_date.isoformat(),
            "location": self.location,
            "setupStatus": self.setup_status,
            "autoSendFiles": self.auto_send_files,
            "runStartupEvent": self.run_startup_event,
            "deviceReadyEventPresetID": self.device_ready_event_preset_id,
            "standaloneEventPresetID": self.standalone_event_preset_id,
            "logHealth": self.log_health,
            "runAnalytics": self.run_analytics,
            "audioChannelName": self.audio_channel_name,
            "volume": self.volume,
            "commentListID": self.comment_list_id,
            "isArchived": self.is_archived,
            "gUID": self.guid,
            "creationDate": self.creation_date.isoformat(),
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date.isoformat(),
            "lastModifiedBy": self.last_modified_by
        }

    def to_json(self):
        return json.dumps(self.to_dict())
