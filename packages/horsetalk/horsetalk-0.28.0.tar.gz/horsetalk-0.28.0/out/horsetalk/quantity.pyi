from _typeshed import Incomplete
from typing import Self

ureg: Incomplete
Q_: Incomplete

class HorsetalkQuantity(Q_):
    REGEX: str
    def __new__(cls, *args, **kwargs) -> Self: ...
    def __getattr__(self, attr): ...
