from peak_utility.enumeration.parsing_enum import ParsingEnum

class RacecourseStyle(ParsingEnum):
    UNKNOWN: int
    GALLOPING: int
    STIFF: int
    TIGHT: int
    SHARP = TIGHT
