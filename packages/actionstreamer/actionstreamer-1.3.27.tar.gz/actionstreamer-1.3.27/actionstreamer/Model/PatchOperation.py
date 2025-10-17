import json


class PatchOperation:

    def __init__(
            self,
            value,
            field_name: str = '',
            **kwargs
        ):
        
        self.field_name = field_name
        self.value = value

        camel_to_snake = {
            "fieldName": "field_name",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "operation": '',
            "fieldName": self.field_name,
            "value": self.value
        }

    def to_json(self):
        return json.dumps(self.to_dict())