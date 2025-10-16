from .surface import Surface as Surface
from peak_utility.enumeration.parsing_enum import ParsingEnum

class GoingDescription(ParsingEnum):
    @property
    def surface(self): ...
