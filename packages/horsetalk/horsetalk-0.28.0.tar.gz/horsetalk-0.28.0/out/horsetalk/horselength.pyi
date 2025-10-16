from decimal import Decimal
from enum import Enum
from typing import Self

class Horselength(Decimal):
    class Description(Enum):
        DEAD_HEAT = 0
        NOSE = 0.05
        SHORT_HEAD = 0.1
        HEAD = 0.2
        SHORT_NECK = 0.25
        NECK = 0.3
        DISTANCE = 100
        DHT = DEAD_HEAT
        NS = NOSE
        NSE = NOSE
        SHD = SHORT_HEAD
        HD = HEAD
        SNK = SHORT_NECK
        NK = NECK
        DIST = DISTANCE
        DST = DISTANCE
    def __new__(cls, value: float | Decimal | str | None = None) -> Self: ...
    def __add__(self, other: Decimal | int) -> Horselength: ...
    def __radd__(self, other: Decimal | int) -> Horselength: ...
    def __sub__(self, other: Decimal | int) -> Horselength: ...
    def __rsub__(self, other: Decimal | int) -> Horselength: ...
