import json


class ReceiveUDPAudioArgs:

    def __init__(
        self,
        sender_device_id: int = 0,
        port: int = 0,
        **kwargs
    ):
        self.sender_device_id = sender_device_id
        self.port = port

        camel_to_snake = {
            "senderDeviceID": "sender_device_id"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "senderDeviceID": self.sender_device_id,
            "port": self.port
        }

    def to_json(self):
        return json.dumps(self.to_dict())
