from _typeshed import Incomplete
from peak_utility.enumeration.parsing_enum import ParsingEnum

class Silks:
    description: str
    class Colour(ParsingEnum):
        BEIGE: int
        BLACK: int
        BROWN: int
        DARK_BLUE: int
        DARK_GREEN: int
        EMERALD_GREEN: int
        GREEN: int
        GREY: int
        LIGHT_BLUE: int
        LIGHT_GREEN: int
        MAROON: int
        MAUVE: int
        ORANGE: int
        PINK: int
        PURPLE: int
        RED: int
        ROYAL_BLUE: int
        WHITE: int
        YELLOW: int
        @staticmethod
        def phrases(): ...
    class Pattern(ParsingEnum):
        ARMLETS: int
        ARMLET = ARMLETS
        BRACES: int
        CHECK: int
        CHECKED = CHECK
        CHEVRON: int
        CHEVRONS: int
        CROSS_BELTS: int
        CROSS_OF_LORRAINE: int
        CROSS_SASHES = CROSS_BELTS
        CUFFS: int
        DIAMOND: int
        DIAMONDS: int
        DIABOLO: int
        DISC: int
        EPAULETS: int
        HALVED: int
        HOLLOW_BOX: int
        HOOP: int
        HOOPS: int
        HOOPED = HOOPS
        INVERTED_TRIANGLE: int
        LARGE_SPOTS: int
        PANEL: int
        PLAIN: int
        QUARTERED: int
        SASH: int
        SEAMS: int
        SPOTS: int
        STAR: int
        STARS: int
        STRIPE: int
        STRIPES: int
        STRIPED = STRIPES
        TRIPLE_DIAMOND: int
        @staticmethod
        def phrases(): ...
        @classmethod
        def body_only(cls): ...
    class Element:
        primary: Incomplete
        secondary: Incomplete
        pattern: Incomplete
        def __init__(self, primary: Silks.Colour, secondary: Silks.Colour | None = None, pattern: Silks.Pattern | None = None) -> None: ...
        def __eq__(self, other): ...
    @classmethod
    def parse(cls, description: str) -> Silks: ...
    @property
    def body(self) -> Silks.Element: ...
    @property
    def cap(self) -> Silks.Element: ...
    @property
    def sleeves(self) -> Silks.Element: ...
