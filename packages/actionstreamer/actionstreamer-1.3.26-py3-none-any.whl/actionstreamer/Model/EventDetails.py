import json


class EventDetails:

    def __init__(
        self,
        event_id: int = 0,
        event_status: int = 0,
        event_parameters: str = '',
        result: str = '',
        percent_complete: float = 0.0,
        priority: int = 0,
        attempt_number: int = 0,
        max_attempts: int = 0,
        tag_string: str = '',
        tag_number: int = 0,
        **kwargs
    ):
        self.event_id = event_id
        self.event_status = event_status
        self.event_parameters = event_parameters
        self.result = result
        self.percent_complete = percent_complete
        self.priority = priority
        self.attempt_number = attempt_number
        self.max_attempts = max_attempts
        self.tag_string = tag_string
        self.tag_number = tag_number

        camel_to_snake = {
            "eventID": "event_id",
            "eventStatus": "event_status",
            "eventParameters": "event_parameters",
            "percentComplete": "percent_complete",
            "attemptNumber": "attempt_number",
            "maxAttempts": "max_attempts",
            "tagString": "tag_string",
            "tagNumber": "tag_number"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "eventID": self.event_id,
            "eventStatus": self.event_status,
            "eventParameters": self.event_parameters,
            "result": self.result,
            "percentComplete": self.percent_complete,
            "priority": self.priority,
            "attemptNumber": self.attempt_number,
            "maxAttempts": self.max_attempts,
            "tagString": self.tag_string,
            "tagNumber": self.tag_number
        }

    def to_json(self):
        return json.dumps(self.to_dict())
