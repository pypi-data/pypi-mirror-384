from . import Event

class EventWithNames(Event):

    def __init__(
        self,
        key: int = 0,
        user_id: int = 0,
        device_id: int = 0,
        agent_type_id: int = 0,
        agent_id: int = 0,
        event_type_id: int = 0,
        server_event: int = 0,
        event_status: int = 0,
        event_parameters: str = '',
        process_id: int = 0,
        result: str = '',
        percent_complete: int = 0,
        priority: int = 0,
        expiration_epoch: int = 0,
        attempt_number: int = 0,
        max_attempts: int = 0,
        checkout_token: str = '',
        tag_string: str = '',
        tag_number: int = 0,
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        device_name: str = '',
        event_type: str = '',
        agent_type: str = '',
        version: str = '',
        event_status_name: str = '',
        event_status_description: str = '',
        agent_index: int = 0,
        **kwargs
    ):
        camel_to_snake = {
            "deviceName": "device_name",
            "eventType": "event_type",
            "agentType": "agent_type",
            "eventStatusName": "event_status_name",
            "eventStatusDescription": "event_status_description",
            "agentIndex": "agent_index",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        # Call parent constructor
        super().__init__(
            key, user_id, device_id, agent_type_id, agent_id, event_type_id,
            server_event, event_status, event_parameters, process_id, result,
            percent_complete, priority, expiration_epoch, attempt_number,
            max_attempts, checkout_token, tag_string, tag_number,
            creation_date, created_by, last_modified_date, last_modified_by,
            **kwargs
        )

        # Ensure defaults or values set via setattr
        self.device_name = getattr(self, "device_name", device_name)
        self.event_type = getattr(self, "event_type", event_type)
        self.agent_type = getattr(self, "agent_type", agent_type)
        self.version = version
        self.event_status_name = getattr(self, "event_status_name", event_status_name)
        self.event_status_description = getattr(self, "event_status_description", event_status_description)
        self.agent_index = getattr(self, "agent_index", agent_index)
