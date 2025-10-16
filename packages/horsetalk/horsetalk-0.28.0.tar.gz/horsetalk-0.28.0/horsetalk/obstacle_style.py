from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class ObstacleStyle(ParsingEnum):
    """
    An enumeration representing the style of an inividual obstacle.

    """

    HURDLE = 1
    PLAIN_FENCE = 2
    OPEN_DITCH = 3
    WATER_JUMP = 4
    SPECIALIST = 5

    # Abbreviations
    PLAIN = PLAIN_FENCE
    DITCH = OPEN_DITCH
    WATER = WATER_JUMP
