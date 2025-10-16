from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class JockeyExperienceLevel(ParsingEnum):
    """
    An enumeration that represents a jockey's experience level.

    """

    AMATEUR = 1
    CONDITIONAL = 2
    APPRENTICE = 3
    PROFESSIONAL = 4

    # Plurals
    AMATEURS = AMATEUR
    CONDITIONALS = CONDITIONAL
    APPRENTICES = APPRENTICE
    PROFESSIONALS = PROFESSIONAL
