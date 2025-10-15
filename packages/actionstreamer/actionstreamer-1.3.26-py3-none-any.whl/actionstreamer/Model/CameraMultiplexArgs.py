import json


class CameraMultiplexArgs:

    def __init__(
        self,
        height: int = 1920,
        width: int = 1080,
        fps: float = 30,
        device_id: int = 0,
        **kwargs
    ):
        self.height = height
        self.width = width
        self.fps = fps
        self.device_id = device_id

        camel_to_snake = {
            "deviceID": "device_id"
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
            "deviceID": self.device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
