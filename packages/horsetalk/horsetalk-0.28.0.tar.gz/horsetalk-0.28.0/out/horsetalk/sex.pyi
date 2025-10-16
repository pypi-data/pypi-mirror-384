from peak_utility.enumeration.parsing_enum import ParsingEnum

class Sex(ParsingEnum):
    MALE: int
    FEMALE: int
    M = MALE
    XY = MALE
    F = FEMALE
    XX = FEMALE
