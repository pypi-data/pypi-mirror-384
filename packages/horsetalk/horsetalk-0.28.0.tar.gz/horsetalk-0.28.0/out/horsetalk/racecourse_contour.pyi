from peak_utility.enumeration.parsing_enum import ParsingEnum

class RacecourseContour(ParsingEnum):
    UNKNOWN: int
    FLAT: int
    DOWNHILL: int
    UPHILL: int
    UNDULATING: int
    DOWN = DOWNHILL
    UP = UPHILL
