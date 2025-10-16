from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class RacingCode(ParsingEnum):
    """
    An enumeration that represents a code of racing.

    """

    FLAT = 1
    NATIONAL_HUNT = 2
    POINT_TO_POINT = 3

    # Abbreviations
    F = FLAT
    N = NATIONAL_HUNT
    NH = NATIONAL_HUNT
    P = POINT_TO_POINT
    PTP = POINT_TO_POINT
    P2P = POINT_TO_POINT
