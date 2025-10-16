from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class Hemisphere(ParsingEnum):
    """
    An enumeration representing the geographical hemisphere.

    """

    NORTHERN = 1
    SOUTHERN = 2

    # Abbreviations
    N = NORTHERN
    S = SOUTHERN
    NORTH = NORTHERN
    SOUTH = SOUTHERN
