import re
from typing import Self, cast

from pint import UnitRegistry

ureg = UnitRegistry(fmt_locale="en_GB")
ureg.define("hand = 4 * inch = hh")
ureg.define("furlong = 0.125 * mile = f")
ureg.define("@alias yard = y")
Q_ = ureg.Quantity


class HorsetalkQuantity(Q_):  # type: ignore
    REGEX = r"(\d+(?:\.\d+)?\D+)"

    def __new__(cls, *args, **kwargs) -> Self:
        """
        Initializes a HorsetalkQuantity object.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            A HorsetalkQuantity object.
        """
        if args and isinstance(args[0], str):
            arg = args[0].replace(",", "")
            if not (match := re.fullmatch(cls.REGEX, arg)):
                raise AttributeError(
                    f"Invalid {cls.__name__.lower()} string: {args[0]}"
                )

            parts = match.groups()
            args = cls._string_arg_handler(parts)

        if not args:
            args = next(iter(kwargs.items()), ())[::-1]

        instance = Q_.__new__(Q_, *args)
        instance.__class__ = cls
        return cast(Self, instance)

    def __repr__(self) -> str:
        """
        Returns:
            A representation of a HorsetalkQuantity object.
        """
        return f"<{self.__class__.__name__}: {self!s}>"

    def __getattr__(self, attr):
        return self.to(attr).magnitude

    @classmethod
    def _string_arg_handler(cls, parts):
        return parts
