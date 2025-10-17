import json


class CreateVideoClip:

    def __init__(
        self,
        device_id: int = 0,
        device_name: str = '',
        local_file_path: str = '',
        height: int = 0,
        width: int = 0,
        frames_per_second: float = 0.0,
        start_time: int = 0,
        start_time_ms: int = 0,
        clip_length_in_seconds: float = 0.0,
        video_clip_status: int = 0,
        video_clip_type_id: int = 0,
        video_clip_parameters: str = '',
        **kwargs
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.local_file_path = local_file_path
        self.height = height
        self.width = width
        self.frames_per_second = frames_per_second
        self.start_time = start_time
        self.start_time_ms = start_time_ms
        self.clip_length_in_seconds = clip_length_in_seconds
        self.video_clip_status = video_clip_status
        self.video_clip_type_id = video_clip_type_id
        self.video_clip_parameters = video_clip_parameters

        camel_to_snake = {
            "deviceID": "device_id",
            "deviceName": "device_name",
            "localFilePath": "local_file_path",
            "framesPerSecond": "frames_per_second",
            "startTime": "start_time",
            "startTimeMs": "start_time_ms",
            "clipLengthInSeconds": "clip_length_in_seconds",
            "videoClipStatus": "video_clip_status",
            "videoClipTypeID": "video_clip_type_id",
            "videoClipParameters": "video_clip_parameters"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "deviceID": self.device_id,
            "deviceName": self.device_name,
            "localFilePath": self.local_file_path,
            "height": self.height,
            "width": self.width,
            "framesPerSecond": self.frames_per_second,
            "startTime": self.start_time,
            "startTimeMs": self.start_time_ms,
            "clipLengthInSeconds": self.clip_length_in_seconds,
            "videoClipStatus": self.video_clip_status,
            "videoClipTypeID": self.video_clip_type_id,
            "videoClipParameters": self.video_clip_parameters
        }

    def to_json(self):
        return json.dumps(self.to_dict())
