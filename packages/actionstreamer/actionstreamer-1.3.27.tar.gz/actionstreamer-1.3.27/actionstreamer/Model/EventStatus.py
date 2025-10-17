from enum import Enum


class EventStatus(Enum):

    Checked_out = 2
    Complete = 4
    Error = 5
    Pending = 1
    Processing = 3
    Timed_out = 6
    Cancelled = 7