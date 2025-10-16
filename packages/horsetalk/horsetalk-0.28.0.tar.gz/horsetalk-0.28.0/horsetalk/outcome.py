from typing import Self

from .disaster import Disaster
from .finishing_position import FinishingPosition


class Outcome:
    def __init__(self, value: int | str | Disaster | FinishingPosition):
        if not isinstance(value, (Disaster, FinishingPosition)):
            if str(value).isdigit():
                value = FinishingPosition(value)
            else:
                try:
                    value = Disaster[str(value)]  # type: ignore
                except KeyError:
                    raise ValueError(f"Invalid outcome: {value}")

        assert not isinstance(value, str)

        self._value = value

    def __repr__(self) -> str:
        return f"<Outcome: {self._value.name.title() if isinstance(self._value, Disaster) else int(self._value)}>"

    def __str__(self) -> str:
        return (
            self._value.name.title()
            if isinstance(self._value, Disaster)
            else str(self._value)
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(self._value, Disaster):
            return isinstance(getattr(other, "_value", other), Disaster)

        return self._value == getattr(other, "_value", other)

    def __lt__(self, other: Self) -> bool:
        if isinstance(self._value, Disaster):
            return not isinstance(other._value, Disaster)

        return not isinstance(other._value, Disaster) and self._value < other._value

    def __le__(self, other: Self) -> bool:
        return self == other or self < other

    def __gt__(self, other: Self) -> bool:
        if isinstance(self._value, Disaster):
            return False

        return isinstance(other._value, Disaster) or self._value > other._value

    def __ge__(self, other: Self) -> bool:
        return self == other or self > other

    @property
    def is_completion(self) -> bool:
        return isinstance(self._value, FinishingPosition)

    @property
    def is_win(self) -> bool:
        return self._value == FinishingPosition(1)
