import json


class SendActionSyncArgs:

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        video: int = 0,
        audio: int = 0,
        rotation_degrees: int = 0,
        device_ip: str = '',
        receiver_device_id: str = '',
        device_port: int = 0,
        fps: float = 30.0,
        bitrate: int = 0,
        **kwargs
    ):
        self.width = width
        self.height = height
        self.video = video
        self.audio = audio
        self.rotation_degrees = rotation_degrees
        self.device_ip = device_ip
        self.receiver_device_id = receiver_device_id
        self.device_port = device_port
        self.fps = fps
        self.bitrate = bitrate

        camel_to_snake = {
            "rotationDegrees": "rotation_degrees",
            "deviceIP": "device_ip",
            "receiverDeviceID": "receiver_device_id",
            "devicePort": "device_port"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "video": self.video,
            "audio": self.audio,
            "rotationDegrees": self.rotation_degrees,
            "deviceIP": self.device_ip,
            "receiverDeviceID": self.receiver_device_id,
            "devicePort": self.device_port,
            "fps": self.fps,
            "bitrate": self.bitrate
        }

    def to_json(self):
        return json.dumps(self.to_dict())
