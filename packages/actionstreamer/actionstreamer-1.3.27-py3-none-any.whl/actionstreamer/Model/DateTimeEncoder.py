import datetime
from json import JSONEncoder


class DateTimeEncoder(JSONEncoder):

    # Override the default method
    def default(self, obj) -> str | None:
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        