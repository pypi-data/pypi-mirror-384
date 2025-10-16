from .age_category import AgeCategory as AgeCategory
from .gender import Gender as Gender
from .horse_experience_level import HorseExperienceLevel as HorseExperienceLevel
from .jump_category import JumpCategory as JumpCategory
from .race_designation import RaceDesignation as RaceDesignation

class RaceTitle:
    @classmethod
    def parse(cls, title: str) -> dict: ...
