import json


class Notification:

    def __init__(
        self,
        notification_id: int = 0,
        notification_status_id: int = 0,
        user_id: int = 0,
        message: str = '',
        seen_in_app: bool = False,
        seen_date: str = '',
        sent_as_email: bool = False,
        sent_as_email_date: str = '',
        guid: str = '',
        is_archived: bool = False,
        creation_date: str = '',
        created_by: int = 0,
        last_modified_date: str = '',
        last_modified_by: int = 0,
        **kwargs
    ):
        self.notification_id = notification_id
        self.notification_status_id = notification_status_id
        self.user_id = user_id
        self.message = message
        self.seen_in_app = seen_in_app
        self.seen_date = seen_date
        self.sent_as_email = sent_as_email
        self.sent_as_email_date = sent_as_email_date
        self.guid = guid
        self.is_archived = is_archived
        self.creation_date = creation_date
        self.created_by = created_by
        self.last_modified_date = last_modified_date
        self.last_modified_by = last_modified_by

        camel_to_snake = {
            "key": "notification_id",
            "notificationStatusID": "notification_status_id",
            "userID": "user_id",
            "seenInApp": "seen_in_app",
            "seenDate": "seen_date",
            "sentAsEmail": "sent_as_email",
            "sentAsEmailDate": "sent_as_email_date",
            "isArchived": "is_archived",
            "creationDate": "creation_date",
            "createdBy": "created_by",
            "lastModifiedDate": "last_modified_date",
            "lastModifiedBy": "last_modified_by"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "key": self.notification_id,
            "notificationStatusID": self.notification_status_id,
            "userID": self.user_id,
            "message": self.message,
            "seenInApp": self.seen_in_app,
            "seenDate": self.seen_date,
            "sentAsEmail": self.sent_as_email,
            "sentAsEmailDate": self.sent_as_email_date,
            "guid": self.guid,
            "isArchived": self.is_archived,
            "creationDate": self.creation_date,
            "createdBy": self.created_by,
            "lastModifiedDate": self.last_modified_date,
            "lastModifiedBy": self.last_modified_by
        }

    def to_json(self):
        return json.dumps(self.to_dict())
