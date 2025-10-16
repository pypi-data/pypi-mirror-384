from peak_utility.enumeration.parsing_enum import ParsingEnum

class RacecourseShape(ParsingEnum):
    UNKNOWN: int
    STRAIGHT: int
    HORSESHOE: int
    TRIANGLE: int
    OVAL: int
    PEAR: int
    CIRCLE: int
    ROUND = OVAL
    TRIANGULAR = TRIANGLE
