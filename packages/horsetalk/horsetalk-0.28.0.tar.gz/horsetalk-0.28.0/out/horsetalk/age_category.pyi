from .age_restriction import AgeRestriction as AgeRestriction
from peak_utility.enumeration.parsing_enum import ParsingEnum

class AgeCategory(ParsingEnum):
    JUVENILE: int
    VETERAN: int
    VETERANS = VETERAN
    def to_age_restriction(self) -> AgeRestriction: ...
