from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class HorseExperienceLevel(ParsingEnum):
    """
    An enumeration that represents a horse's experience level.

    """

    MAIDEN = 1
    NOVICE = 2
    BEGINNER = 3

    # Alternatives
    NOV = NOVICE
    NOVICES = NOVICE
    BEGINNERS = BEGINNER
