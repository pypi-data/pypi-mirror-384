import json


class MultiplexStopRecordingArgs:

    def __init__(
            self, 
            device_id: int = 0, 
            **kwargs
    ):
        self.device_id = device_id

        if "deviceID" in kwargs:
            self.device_id = kwargs.pop("deviceID")

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "deviceID": self.device_id
        }

    def to_json(self):
        return json.dumps(self.to_dict())
