from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class StallsPosition(ParsingEnum):
    INSIDE = 1
    CENTRE = 2
    OUTSIDE = 3

    # Alternatives
    FAR = INSIDE
    MIDDLE = CENTRE
    NEAR = OUTSIDE
