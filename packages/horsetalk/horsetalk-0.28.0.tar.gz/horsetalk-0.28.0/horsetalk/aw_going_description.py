from .going_description import GoingDescription


class AWGoingDescription(GoingDescription):
    """
    An enumeration that represents a scale of UK and Ireland all-weather going descriptions.

    """

    SLOW = 6
    STANDARD_TO_SLOW = 7
    STANDARD = 8
    STANDARD_TO_FAST = 9
    FAST = 10

    # Abbreviations
    SLW = SLOW
    STS = STANDARD_TO_SLOW
    STD = STANDARD
    STF = STANDARD_TO_FAST
    FST = FAST
