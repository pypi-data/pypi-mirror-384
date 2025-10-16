from peak_utility.enumeration.parsing_enum import ParsingEnum

class StallsPosition(ParsingEnum):
    INSIDE: int
    CENTRE: int
    OUTSIDE: int
    FAR = INSIDE
    MIDDLE = CENTRE
    NEAR = OUTSIDE
