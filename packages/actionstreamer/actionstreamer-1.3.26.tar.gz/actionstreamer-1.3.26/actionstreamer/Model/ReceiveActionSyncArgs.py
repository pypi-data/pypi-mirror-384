import json


class ReceiveActionSyncArgs:

    def __init__(
        self,
        buffer_ms: int = 200,
        video: int = 0,
        audio: int = 0,
        rotation_degrees: int = 0,
        filename: str = '',
        device_ip: str = '',
        device_port: int = 0,
        card_id: int = 0,
        card_device_id: int = 0,
        sender_device_id: int = 0,
        **kwargs
    ):
        self.buffer_ms = buffer_ms
        self.video = video
        self.audio = audio
        self.rotation_degrees = rotation_degrees
        self.filename = filename
        self.device_ip = device_ip
        self.device_port = device_port
        self.card_id = card_id
        self.card_device_id = card_device_id
        self.sender_device_id = sender_device_id

        camel_to_snake = {
            "bufferMs": "buffer_ms",
            "rotationDegrees": "rotation_degrees",
            "deviceIP": "device_ip",
            "devicePort": "device_port",
            "cardID": "card_id",
            "cardDeviceID": "card_device_id",
            "senderDeviceID": "sender_device_id",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "bufferMs": self.buffer_ms,
            "video": self.video,
            "audio": self.audio,
            "rotationDegrees": self.rotation_degrees,
            "filename": self.filename,
            "deviceIP": self.device_ip,
            "devicePort": self.device_port,
            "cardID": self.card_id,
            "cardDeviceID": self.card_device_id,
            "senderDeviceID": self.sender_device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
