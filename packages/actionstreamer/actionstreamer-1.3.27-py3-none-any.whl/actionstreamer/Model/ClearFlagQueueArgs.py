import json


class ClearFlagQueueArgs:

    def __init__(
            self, 
            flag_queue_name: str = '', 
            **kwargs
    ):
        self.flag_queue_name = flag_queue_name

        if "flagQueueName" in kwargs:
            self.flag_queue_name = kwargs.pop("flagQueueName")

        camel_to_snake = {
            "flagQueueName": "flag_queue_name"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "flagQueueName": self.flag_queue_name
        }

    def to_json(self):
        return json.dumps(self.to_dict())
