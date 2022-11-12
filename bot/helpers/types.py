from enum import Enum, auto


class IndicatorType(Enum):
    LOCATION = auto()
    MOMENTUM_PRICE = auto()
    MOMENTUM_VOLUME = auto()
    MOMENTUM_OSCILLATOR = auto()
    STRUCTURE = auto()
    TREND = auto()


class ExtremaType(Enum):
    HIGHS = auto()
    LOWS = auto()


class ExtremaDirection(Enum):
    HIGHER = auto()
    LOWER = auto()
