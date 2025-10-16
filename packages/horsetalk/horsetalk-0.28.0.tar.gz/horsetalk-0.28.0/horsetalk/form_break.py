from enum import Enum


class FormBreak(Enum):
    """
    An enumeration that represents a break in a horse's form.

    """

    YEAR = "-"
    SEASON = "/"

    def __str__(self):
        return self.value
