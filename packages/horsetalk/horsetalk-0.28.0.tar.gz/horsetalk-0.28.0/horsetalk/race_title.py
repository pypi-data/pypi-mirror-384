from enum import Enum
from itertools import pairwise

from .age_category import AgeCategory
from .gender import Gender
from .horse_experience_level import HorseExperienceLevel
from .jump_category import JumpCategory
from .race_designation import RaceDesignation


class RaceTitle:
    """
    A class for parsing a race title into its component parts.

    Methods:
        parse(title: str) -> dict: Parses a race title into component parts and returns a dictionary.
        _lookup(enum: type[Enum], allow_multiple: bool = False) -> list[Enum] | Enum | None:
            Private method to lookup an Enum value from a list of words.

    """

    @classmethod
    def parse(cls, title: str) -> dict:
        """Parses a race title into component parts.

        Args:
            title: A race title.

        Returns:
            dict: A dictionary of component parts.
        """
        words = title.split()

        enums = [
            AgeCategory,
            HorseExperienceLevel,
            Gender,
            JumpCategory,
            RaceDesignation,
        ]
        end_index = -1
        for i, word in enumerate(words):
            if any(getattr(enum, word, None) is not None for enum in enums):
                end_index = i
                break
        name = " ".join(words[:end_index])

        return {
            "age_category": cls._lookup(AgeCategory, words),
            "horse_experience_level": cls._lookup(HorseExperienceLevel, words),
            "gender": cls._lookup(Gender, words, allow_multiple=True),
            "jump_category": cls._lookup(JumpCategory, words),
            "race_designation": cls._lookup(
                RaceDesignation, words, allow_multiple=True
            ),
            "name": name,
        }

    @classmethod
    def _lookup(
        cls, enum: type[Enum], words: list[str], *, allow_multiple: bool = False
    ) -> list[Enum] | Enum | None:
        """Private method to lookup an enum value from a list of words.

        Args:
            enum (type[Enum]): The Enum to search through.
            allow_multiple (bool, optional): Whether or not to allow multiple Enum values to be returned. Defaults to False.

        Returns:
            Union[list[Enum], Enum, None]: The found Enum value or None.

        """
        checklist = words + ["_".join(pair) for pair in pairwise(words)]
        found_values = [
            found_value
            for word in checklist
            if (found_value := getattr(enum, word, None)) is not None
        ]
        return (
            None
            if not found_values
            else found_values
            if allow_multiple
            else found_values[-1]
        )
