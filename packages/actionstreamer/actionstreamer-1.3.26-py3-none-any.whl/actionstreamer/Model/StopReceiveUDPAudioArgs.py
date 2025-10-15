import json


class StopReceiveUDPAudioArgs:

    def __init__(
            self, 
            sender_device_id: int = 0,
            **kwargs
    ):
        self.sender_device_id = sender_device_id

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
            "senderDeviceID": self.sender_device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
