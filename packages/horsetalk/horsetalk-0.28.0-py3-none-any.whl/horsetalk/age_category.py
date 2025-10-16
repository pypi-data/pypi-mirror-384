from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore

from .age_restriction import AgeRestriction


class AgeCategory(ParsingEnum):
    """
    An enumeration that represents the age category of a horse.

    """

    JUVENILE = 1
    VETERAN = 2

    # Alternatives
    VETERANS = VETERAN

    def to_age_restriction(self) -> AgeRestriction:
        """
        Implied age restriction, based on the category name.

        Returns:
            An AgeRestriction instance representing the age restriction of the category.

        """

        return AgeRestriction({"JUVENILE": "4yo", "VETERAN": "10yo+"}[self.name])
