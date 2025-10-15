import json


class StopReceiveActionSyncArgs:

    def __init__(
            self, 
            sender_ip: str = '',
            sender_port: int = 0,
            **kwargs
    ):
        self.sender_ip = sender_ip
        self.sender_port = sender_port

        camel_to_snake = {
            "senderIP": "sender_ip",
            "senderPort": "sender_port"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "senderIP": self.sender_ip,
            "senderPort": self.sender_port
        }

    def to_json(self):
        return json.dumps(self.to_dict())
