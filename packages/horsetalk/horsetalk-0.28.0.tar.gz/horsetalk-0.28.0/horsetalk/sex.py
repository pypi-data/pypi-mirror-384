from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class Sex(ParsingEnum):
    """
    An enumeration representing the sex of a horse.

    """

    MALE = 1
    FEMALE = 2

    # Abbreviations
    M = MALE
    XY = MALE
    F = FEMALE
    XX = FEMALE
