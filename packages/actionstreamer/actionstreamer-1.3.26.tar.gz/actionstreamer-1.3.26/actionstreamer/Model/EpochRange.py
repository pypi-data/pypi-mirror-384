import json


class EpochRange:

    def __init__(
            self, 
            start_epoch: int = 0, 
            end_epoch: int = 0, 
            **kwargs
    ):
        self.start_epoch = start_epoch
        self.end_epoch = end_epoch

        camel_to_snake = {
            "startEpoch": "start_epoch",
            "endEpoch": "end_epoch"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "startEpoch": self.start_epoch,
            "endEpoch": self.end_epoch
        }

    def to_json(self):
        return json.dumps(self.to_dict())
