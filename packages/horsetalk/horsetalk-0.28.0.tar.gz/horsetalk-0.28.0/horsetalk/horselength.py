from decimal import Decimal, InvalidOperation
from enum import Enum
from fractions import Fraction
from typing import Optional, Self


class Horselength(Decimal):
    """
    A Decimal subclass that represents a distance in horse lengths.

    Horse lengths are commonly used to measure the distance between horses in a race.
    """

    class Description(Enum):
        """
        An enumeration that represents some commonly used lengths in horse racing,
        with their corresponding values.

        Abbreviations can also be used to reference these lengths.
        """

        DEAD_HEAT = 0
        NOSE = 0.05
        SHORT_HEAD = 0.1
        HEAD = 0.2
        SHORT_NECK = 0.25
        NECK = 0.3
        DISTANCE = 100

        # Abbreviations
        DHT = DEAD_HEAT
        NS = NOSE
        NSE = NOSE
        SHD = SHORT_HEAD
        HD = HEAD
        SNK = SHORT_NECK
        NK = NECK
        DIST = DISTANCE
        DST = DISTANCE

    def __new__(cls, value: Optional[float | Decimal | str] = None) -> Self:
        """Create a new horselength instance

        :param value: Either a description or a number, representing the horselength, defaults to None
        :type value: Optional[float | Decimal |  str], optional
        :raises ValueError: For invalid inputs
        :return: A new horselength instance
        :rtype: Self
        """
        value = str(value or 0)
        if "/" in value:
            parts = value.split(" ")
            whole = parts[0] if len(parts) == 2 else 0
            fraction = Fraction(parts[-1])
            value = Decimal(str(whole)) + Decimal(fraction.numerator) / Decimal(
                fraction.denominator
            )
        elif value.upper() in cls.Description.__members__:
            value = str(cls.Description[value.upper()].value)

        try:
            return super().__new__(cls, value)
        except InvalidOperation:
            raise ValueError(f"Invalid input value for Horselength: {value}")

    def __repr__(self) -> str:
        """
        Return a representation of the Horselength instance.
        """
        return f"<Horselength: {self}>"

    def __str__(self) -> str:
        """
        Return a string representation of the Horselength instance.
        """
        if self % 1 == 0:
            return super().__str__()

        for e in Horselength.Description:
            if self == Decimal(str(e.value)):
                return e.name.lower()

        whole = self // 1
        fraction = Fraction(str(self % 1))
        return f"{whole} {fraction}" if whole else str(fraction)

    def __add__(self, other: Decimal | int) -> "Horselength":
        """
        Adds two Horselength instances or an instance and a Decimal and returns a Horselength.
        """
        sum = super().__add__(other)
        return Horselength(sum)

    def __radd__(self, other: Decimal | int) -> "Horselength":
        """
        Adds two Horselength instances or an instance and a Decimal and returns a Horselength.
        """
        sum = super().__radd__(other)
        return Horselength(sum)

    def __sub__(self, other: Decimal | int) -> "Horselength":
        """
        Subtracts two Horselength instances or an instance and a Decimal and returns a Horselength.
        """
        diff = super().__sub__(other)
        return Horselength(diff)

    def __rsub__(self, other: Decimal | int) -> "Horselength":
        """
        Subtracts two Horselength instances or an instance and a Decimal and returns a Horselength.
        """
        diff = super().__rsub__(other)
        return Horselength(diff)
