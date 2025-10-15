import json


class TranscodingArgs:

    def __init__(
            self, 
            file_id: int = 0, 
            source: str = '', 
            source_file: str = '', 
            target_file: str = '', 
            fps: float = 0.0, 
            codec: str = '', 
            **kwargs
    ):
        self.file_id = file_id
        self.source = source
        self.source_file = source_file
        self.target_file = target_file
        self.fps = fps
        self.codec = codec

        camel_to_snake = {
            "fileID": "file_id",
            "sourceFile": "source_file",
            "targetFile": "target_file"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "fileID": self.file_id,
            "source": self.source,
            "sourceFile": self.source_file,
            "targetFile": self.target_file,
            "fps": self.fps,
            "codec": self.codec
        }

    def to_json(self):
        return json.dumps(self.to_dict())
