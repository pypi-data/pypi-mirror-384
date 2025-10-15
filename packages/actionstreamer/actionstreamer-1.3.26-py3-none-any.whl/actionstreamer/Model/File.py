import json


class File:

    def __init__(
        self,
        key: int = 0,
        user_id: int = 0,
        device_id: int = 0,
        filename: str = '',
        file_guid: str = '',
        sha256_hash: str = '',
        file_location: str = '',
        file_expiration: str = '',
        file_size: int = 0,
        file_in_s3: bool = False,
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs
    ):
        self.key = key
        self.user_id = user_id
        self.device_id = device_id
        self.filename = filename
        self.file_guid = file_guid
        self.sha256_hash = sha256_hash
        self.file_location = file_location
        self.file_expiration = file_expiration
        self.file_size = file_size
        self.file_in_s3 = file_in_s3
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "userID": "user_id",
            "deviceID": "device_id",
            "fileGUID": "file_guid",
            "sHA256Hash": "sha256_hash",
            "fileLocation": "file_location",
            "fileExpiration": "file_expiration",
            "fileSize": "file_size",
            "fileInS3": "file_in_s3",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.key,
            "userID": self.user_id,
            "deviceID": self.device_id,
            "filename": self.filename,
            "fileGUID": self.file_guid,
            "sHA256Hash": self.sha256_hash,
            "fileLocation": self.file_location,
            "fileExpiration": self.file_expiration,
            "fileSize": self.file_size,
            "fileInS3": self.file_in_s3,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by,
        }

    def to_json(self):
        return json.dumps(self.to_dict())
