from peak_utility.enumeration.parsing_enum import ParsingEnum

class RacingCode(ParsingEnum):
    FLAT: int
    NATIONAL_HUNT: int
    POINT_TO_POINT: int
    F = FLAT
    N = NATIONAL_HUNT
    NH = NATIONAL_HUNT
    P = POINT_TO_POINT
    PTP = POINT_TO_POINT
    P2P = POINT_TO_POINT
