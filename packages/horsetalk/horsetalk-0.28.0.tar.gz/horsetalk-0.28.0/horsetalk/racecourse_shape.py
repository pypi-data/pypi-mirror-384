from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class RacecourseShape(ParsingEnum):
    """
    An enumeration representing the shape of a racecourse.

    """

    UNKNOWN = 0
    STRAIGHT = 1
    HORSESHOE = 2
    TRIANGLE = 3
    OVAL = 4
    PEAR = 5
    CIRCLE = 6

    # Alternatives
    ROUND = OVAL
    TRIANGULAR = TRIANGLE
