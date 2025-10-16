from .going_description import GoingDescription


class DirtGoingDescription(GoingDescription):
    """
    An enumeration that represents a scale of US dirt going descriptions.
    """

    MUDDY = 6
    SLOW = 7
    SLOPPY = 7.5
    GOOD = 8
    WET_FAST = 8.5
    SEALED = 9
    FAST = 10
