import json
import actionstreamer.Model

class ConcatenateClipsArgs:

    def __init__(
        self,
        device_id: int = 0,
        device_name: str = '',
        start_epoch: int = 0,
        end_epoch: int = 0,
        upload_url: str = '',
        postback_url: str = '',
        timeout: int = 0,
        video_clips: list = [],
        **kwargs
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.start_epoch = start_epoch
        self.end_epoch = end_epoch
        self.upload_url = upload_url
        self.postback_url = postback_url
        self.timeout = timeout
        self.video_clips = video_clips if video_clips is not None else []

        camel_to_snake = {
            "deviceID": "device_id",
            "deviceName": "device_name",
            "startEpoch": "start_epoch",
            "endEpoch": "end_epoch",
            "uploadURL": "upload_url",
            "postbackURL": "postback_url",
            "videoClips": "video_clips"
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
            "startEpoch": self.start_epoch,
            "endEpoch": self.end_epoch,
            "uploadURL": self.upload_url,
            "postbackURL": self.postback_url,
            "timeout": self.timeout,
            "videoClips": self.video_clips
        }

    def to_json(self):
        return json.dumps(self.to_dict())
