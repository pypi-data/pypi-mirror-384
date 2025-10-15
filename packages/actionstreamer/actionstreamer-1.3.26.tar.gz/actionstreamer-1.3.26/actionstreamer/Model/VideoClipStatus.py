
from enum import Enum

class VideoClipStatus(Enum):

    Announced = 1
    Transferring = 2
    Encoding = 3
    File_available = 4
    Announced_but_missing = 5
    Highlighted = 6