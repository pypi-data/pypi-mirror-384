import json


class SendUDPVideoArgs:

    def __init__(
        self,
        height: int = 1920,
        width: int = 1080,
        fps: float = 30,
        bitrate: int = 5000000,
        receiver_ip_address: str = '',
        port: int = 0,
        **kwargs
    ):
        self.height = height
        self.width = width
        self.fps = fps
        self.bitrate = bitrate
        self.receiver_ip_address = receiver_ip_address
        self.port = port

        camel_to_snake = {
            "receiverIPAddress": "receiver_ip_address"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "height": self.height,
            "width": self.width,
            "fps": self.fps,
            "bitrate": self.bitrate,
            "receiverIPAddress": self.receiver_ip_address,
            "port": self.port
        }

    def to_json(self):
        return json.dumps(self.to_dict())
