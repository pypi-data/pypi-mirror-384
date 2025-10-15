import json


class StandardResult:

    def __init__(
            self, 
            code: str, 
            description: str,
            **kwargs
    ):
        self.code = code
        self.description = description

        camel_to_snake = {
            "code": "code",
            "description": "description"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "code": self.code,
            "description": self.description
        }

    def to_json(self):
        return json.dumps(self.to_dict())
