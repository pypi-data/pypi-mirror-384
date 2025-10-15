import json


class VideoClip:

    def __init__(
        self,
        key: int = 0,
        user_id: int = 0,
        device_id: int = 0,
        file_id: int = 0,
        ts_file_id: int = 0,
        video_clip_type_id: int = 1,
        video_clip_status: int = 0,
        video_clip_parameters: str = '',
        local_file_path: str = '',
        height: int = 0,
        width: int = 0,
        file_size: int = 0,
        frames_per_second: float = 0,
        bitrate: int = 0,
        audio_status: int = 0,
        start_time: int = 0,
        start_time_ms: int = 0,
        end_time: int = 0,
        end_time_ms: int = 0,
        clip_length_in_seconds: float = 0,
        tag_list_id: int = 0,
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs
    ):
        self.key = key
        self.user_id = user_id
        self.device_id = device_id
        self.file_id = file_id
        self.ts_file_id = ts_file_id
        self.video_clip_type_id = video_clip_type_id
        self.video_clip_status = video_clip_status
        self.video_clip_parameters = video_clip_parameters
        self.local_file_path = local_file_path
        self.height = height
        self.width = width
        self.file_size = file_size
        self.frames_per_second = frames_per_second
        self.bitrate = bitrate
        self.audio_status = audio_status
        self.start_time = start_time
        self.start_time_ms = start_time_ms
        self.end_time = end_time
        self.end_time_ms = end_time_ms
        self.clip_length_in_seconds = clip_length_in_seconds
        self.tag_list_id = tag_list_id
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "userID": "user_id",
            "deviceID": "device_id",
            "fileID": "file_id",
            "tSFileID": "ts_file_id",
            "videoClipTypeID": "video_clip_type_id",
            "videoClipStatus": "video_clip_status",
            "videoClipParameters": "video_clip_parameters",
            "localFilePath": "local_file_path",
            "fileSize": "file_size",
            "framesPerSecond": "frames_per_second",
            "audioStatus": "audio_status",
            "startTime": "start_time",
            "startTimeMs": "start_time_ms",
            "endTime": "end_time",
            "endTimeMs": "end_time_ms",
            "clipLengthInSeconds": "clip_length_in_seconds",
            "tagListID": "tag_list_id",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by",
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
            "userID": self.user_id,
            "deviceID": self.device_id,
            "fileID": self.file_id,
            "tSFileID": self.ts_file_id,
            "videoClipTypeID": self.video_clip_type_id,
            "videoClipStatus": self.video_clip_status,
            "videoClipParameters": self.video_clip_parameters,
            "localFilePath": self.local_file_path,
            "height": self.height,
            "width": self.width,
            "fileSize": self.file_size,
            "framesPerSecond": self.frames_per_second,
            "bitrate": self.bitrate,
            "audioStatus": self.audio_status,
            "startTime": self.start_time,
            "startTimeMs": self.start_time_ms,
            "endTime": self.end_time,
            "endTimeMs": self.end_time_ms,
            "clipLengthInSeconds": self.clip_length_in_seconds,
            "tagListID": self.tag_list_id,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by,
        }

    def to_json(self):
        return json.dumps(self.to_dict())
