import json


class WifiConnection:

    def __init__(
            self, 
            ssid: str = '', 
            connection_name: str = '', 
            password: str = '', 
            priority: int = 0, 
            **kwargs
    ):
        self.ssid = ssid
        self.password = password
        self.priority = priority
        self.connection_name = connection_name

        camel_to_snake = {
            "connectionName": "connection_name"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "ssid": self.ssid,
            "connectionName": self.connection_name,
            "password": self.password,
            "priority": self.priority
        }

    def to_json(self):
        return json.dumps(self.to_dict())
