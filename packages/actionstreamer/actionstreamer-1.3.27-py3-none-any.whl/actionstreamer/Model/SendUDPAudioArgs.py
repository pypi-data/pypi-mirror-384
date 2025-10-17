import json


class SendUDPAudioArgs:

    def __init__(
        self,
        receiver_ip_address: str = '',
        port: int = 0,
        sender_device_id: int = 0,
        **kwargs
    ):
        self.receiver_ip_address = receiver_ip_address
        self.port = port
        self.sender_device_id = sender_device_id

        camel_to_snake = {
            "receiverIPAddress": "receiver_ip_address",
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
            "receiverIPAddress": self.receiver_ip_address,
            "port": self.port,
            "senderDeviceID": self.sender_device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
