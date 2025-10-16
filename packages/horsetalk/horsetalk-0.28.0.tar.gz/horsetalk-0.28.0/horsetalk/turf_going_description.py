from .going_description import GoingDescription


class TurfGoingDescription(GoingDescription):
    """
    An enumeration that represents a scale of UK or Ireland turf going descriptions.

    Values are rough equivalents to GoingStick readings.
    """

    HEAVY = 5
    SOFT = 6
    YIELDING_TO_SOFT = 6.5
    GOOD_TO_SOFT = 7
    YIELDING = 7
    GOOD_TO_YIELDING = 7.5
    GOOD = 8
    GOOD_TO_FIRM = 9
    FIRM = 10
    HARD = 11

    # Abbreviations
    V = HEAVY
    HV = HEAVY
    HVY = HEAVY
    S = SOFT
    SFT = SOFT
    D = GOOD_TO_SOFT
    GS = GOOD_TO_SOFT
    YS = YIELDING_TO_SOFT
    Y = YIELDING
    YLD = YIELDING
    GY = GOOD_TO_YIELDING
    G = GOOD
    GD = GOOD
    GF = GOOD_TO_FIRM
    M = GOOD_TO_FIRM
    F = FIRM
    FM = FIRM
    FRM = FIRM
    HD = HARD
    HRD = HARD
