from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore

from .sex import Sex


class Gender(ParsingEnum):
    """
    An enumeration representing the gender of a horse.

    """

    FOAL = 0
    YEARLING = 1
    COLT = 2
    FILLY = 3
    STALLION = 4
    MARE = 5
    GELDING = 6
    RIG = 7
    ENTIRE = 8
    HORSE = 9

    # Abbreviations
    C = COLT
    F = FILLY
    S = STALLION
    M = MARE
    G = GELDING
    R = RIG
    E = ENTIRE
    H = HORSE

    # Plural
    FOALS = FOAL
    YEARLINGS = YEARLING
    COLTS = COLT
    FILLIES = FILLY
    STALLIONS = STALLION
    MARES = MARE
    GELDINGS = GELDING
    RIGS = RIG
    ENTIRES = ENTIRE
    HORSES = HORSE

    @property
    def sex(self):
        """
        Get the sex of the horse based on its gender.

        Raises:
            ValueError: If the gender of the horse is not specific enough to determine its sex.

        Returns:
            Sex: The sex of the horse, either `Sex.FEMALE` or `Sex.MALE`.

        """
        if self in [Gender.FOAL, Gender.YEARLING]:
            raise ValueError("Not enough information to provide sex of horse")

        return Sex.FEMALE if self in [Gender.FILLY, Gender.MARE] else Sex.MALE

    @property
    def has_testes(self):
        """
        Determine if the horse has testes

        Returns:
            bool: True if the horse has testes, False otherwise.

        """
        if self in [Gender.FOAL, Gender.YEARLING]:
            raise ValueError("Not enough information to determine if horse has testes")

        return self.sex == Sex.MALE and self != Gender.GELDING

    @staticmethod
    def determine(official_age: int, sex: Sex | None = None, **kwargs):
        """
        Determine the gender of a horse based on its sex, official age, and optional arguments.

        Args:
            official_age: The official age of the horse in years.
            sex: The sex of the horse.
            **kwargs: Additional keyword arguments that may be used to determine the gender. Accepts is_rig and is_gelded.

        Raises:
            ValueError: If a female horse is specified as a gelding or rig.

        Returns:
            Gender: The gender of the horse based on the input arguments.

        """
        if official_age <= 1:
            return {0: Gender.FOAL, 1: Gender.YEARLING}[official_age]

        testacle_status = (
            "gelding"
            if kwargs.get("is_gelded")
            else "rig"
            if kwargs.get("is_rig")
            else None
        )

        if testacle_status:
            if sex is Sex.FEMALE:
                raise ValueError(f"Female horse cannot be {testacle_status}")
            return Gender[testacle_status]  # type: ignore

        if sex is None:
            raise ValueError("Not enough information to determine gender")

        return {
            True: {Sex.MALE: Gender.COLT, Sex.FEMALE: Gender.FILLY},
            False: {Sex.MALE: Gender.STALLION, Sex.FEMALE: Gender.MARE},
        }[official_age <= 3][sex]
