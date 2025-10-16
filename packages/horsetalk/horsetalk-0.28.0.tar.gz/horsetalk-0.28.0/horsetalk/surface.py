from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class Surface(ParsingEnum):
    """
    An enumeration representing the surface upon which races are held.

    """

    TURF = 1
    DIRT = 2
    ALL_WEATHER = 3
    POLYTRACK = 4
    TAPETA = 5
    FIBRESAND = 6

    # Abbreviations
    T = TURF
    D = DIRT
    AW = ALL_WEATHER
