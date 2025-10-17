import json


class RTMPArgs:

    def __init__(
        self,
        height: int = 1920,
        width: int = 1080,
        fps: float = 30,
        bitrate: int = 5000000,
        server: str = '',
        port: int = 0,
        stream_name: str = '',
        stream_key: str = '',
        hflip: int = 0,
        vflip: int = 0,
        rotation_degrees: int = 0,
        **kwargs
    ):
        self.height = height
        self.width = width
        self.fps = fps
        self.bitrate = bitrate
        self.server = server
        self.port = port
        self.stream_name = stream_name
        self.stream_key = stream_key
        self.hflip = hflip
        self.vflip = vflip
        self.rotation_degrees = rotation_degrees

        camel_to_snake = {
            "streamName": "stream_name",
            "streamKey": "stream_key",
            "rotationDegrees": "rotation_degrees"
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
            "server": self.server,
            "port": self.port,
            "streamName": self.stream_name,
            "streamKey": self.stream_key,
            "hflip": self.hflip,
            "vflip": self.vflip,
            "rotationDegrees": self.rotation_degrees
        }

    def to_json(self):
        return json.dumps(self.to_dict())
