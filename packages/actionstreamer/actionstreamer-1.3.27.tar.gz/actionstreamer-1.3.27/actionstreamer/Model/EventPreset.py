import json


class EventPreset:

    def __init__(
        self,
        device_id: int = 0,
        agent_type: str = '',
        event_type: str = '',
        event_parameters: str = '',
        event_preset_name: str = '',
        priority: int = 1,
        max_attempts: int = 5,
        expiration_epoch: int = 0,
        **kwargs
    ):
        self.device_id = device_id
        self.agent_type = agent_type
        self.event_type = event_type
        self.event_parameters = event_parameters
        self.event_preset_name = event_preset_name
        self.priority = priority
        self.max_attempts = max_attempts
        self.expiration_epoch = expiration_epoch

        camel_to_snake = {
            "deviceID": "device_id",
            "agentType": "agent_type",
            "eventType": "event_type",
            "eventParameters": "event_parameters",
            "eventPresetName": "event_preset_name",
            "maxAttempts": "max_attempts",
            "expirationEpoch": "expiration_epoch"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "deviceID": self.device_id,
            "agentType": self.agent_type,
            "eventType": self.event_type,
            "eventParameters": self.event_parameters,
            "eventPresetName": self.event_preset_name,
            "priority": self.priority,
            "maxAttempts": self.max_attempts,
            "expirationEpoch": self.expiration_epoch
        }

    def to_json(self):
        return json.dumps(self.to_dict())
