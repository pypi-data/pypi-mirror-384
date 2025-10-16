from peak_utility.enumeration.parsing_enum import ParsingEnum

class Handedness(ParsingEnum):
    UNKNOWN: int
    LEFT: int
    RIGHT: int
    BOTH: int
    NEITHER = UNKNOWN
    L = LEFT
    R = RIGHT
    LR = BOTH
    LH = LEFT
    RH = RIGHT
