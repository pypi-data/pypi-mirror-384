from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class Headgear(ParsingEnum):
    """
    An enumeration representing the headgear worn by a horse in a race.

    """

    HOOD = 1
    BLINKERS = 2
    CHEEKPIECES = 3
    TONGUE_TIE = 4
    VISOR = 5
    EYE_HOOD = 6
    EYE_COVER = 7
    EYE_SHIELD = 8

    # Abbreviations
    H = HOOD
    B = BLINKERS
    BL = BLINKERS
    C = CHEEKPIECES
    P = CHEEKPIECES
    T = TONGUE_TIE
    TT = TONGUE_TIE
    V = VISOR
    E = EYE_HOOD
    EC = EYE_COVER
    ES = EYE_SHIELD
