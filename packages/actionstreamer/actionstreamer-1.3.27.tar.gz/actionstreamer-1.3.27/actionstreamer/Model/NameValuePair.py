import json


class NameValuePair:

    def __init__(
            self, 
            name: str = '', 
            value: str = '',
            **kwargs
        ):
        
        self.name = name
        self.value = value

        camel_to_snake = {
            "name": "name",
            "value": "value"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value
        }

    def to_json(self):
        return json.dumps(self.to_dict())
