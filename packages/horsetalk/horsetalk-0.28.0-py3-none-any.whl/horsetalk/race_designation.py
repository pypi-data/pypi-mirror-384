from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class RaceDesignation(ParsingEnum):
    """
    An enumeration representing the designation or type of race.

    """

    HANDICAP = 1
    CONDITIONS = 2
    MAIDEN = 3
    AUCTION = 4
    CLAIMER = 5
    SELLER = 6
    STAKES = 7

    # Abbreviations
    HCAP = HANDICAP
    AU = AUCTION
    CL = CLAIMER
    M = MAIDEN
    S = SELLER
    STKS = STAKES

    # Alternatives
    CLAIMING = CLAIMER
    SELLING = SELLER
    NURSERY = HANDICAP
