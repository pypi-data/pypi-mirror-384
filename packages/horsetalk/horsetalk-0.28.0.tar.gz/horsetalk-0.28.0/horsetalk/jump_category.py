from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class JumpCategory(ParsingEnum):
    """
    An enumeration representing the category of obstacles over which a race is run.

    """

    HURDLE = 1
    STEEPLECHASE = 2
    CROSS_COUNTRY = 3

    # Abbreviations
    H = HURDLE
    HRD = HURDLE
    HRDLE = HURDLE
    C = STEEPLECHASE
    CH = STEEPLECHASE
    CHS = STEEPLECHASE
    CHSE = STEEPLECHASE
    CHASE = STEEPLECHASE
    CC = CROSS_COUNTRY
    XC = CROSS_COUNTRY
