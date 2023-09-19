from enum import Enum, auto


class Mode(Enum):
    SELECT = auto()
    RAIL = auto()
    STATION = auto()
    TRAIN = auto()
    SIGNAL = auto()
    DESTROY = auto()
