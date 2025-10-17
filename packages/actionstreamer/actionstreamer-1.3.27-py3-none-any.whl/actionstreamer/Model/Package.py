import json
from datetime import datetime


class Package:

    def __init__(
        self,
        package_id: int = 0,
        package_type_id: int = 0,
        file_id: int = 0,
        url: str = '',
        encrypted: int = 0,
        package_name: str = '',
        description: str = '',
        version: str = '',
        package_date: datetime = None,
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs
    ):
        self.package_id = package_id
        self.package_type_id = package_type_id
        self.file_id = file_id
        self.url = url
        self.encrypted = encrypted
        self.package_name = package_name
        self.description = description
        self.version = version
        self.package_date = package_date
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "key": "package_id",
            "packageTypeID": "package_type_id",
            "fileID": "file_id",
            "uRL": "url",
            "packageName": "package_name",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by",
            "packageDate": "package_date"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.package_id,
            "packageTypeID": self.package_type_id,
            "fileID": self.file_id,
            "uRL": self.url,
            "encrypted": self.encrypted,
            "packageName": self.package_name,
            "description": self.description,
            "version": self.version,
            "packageDate": self.package_date.isoformat() if self.package_date else None,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by
        }

    def to_json(self):
        return json.dumps(self.to_dict())
