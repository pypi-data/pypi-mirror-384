from peak_utility.enumeration.parsing_enum import ParsingEnum

class RaceDesignation(ParsingEnum):
    HANDICAP: int
    CONDITIONS: int
    MAIDEN: int
    AUCTION: int
    CLAIMER: int
    SELLER: int
    STAKES: int
    HCAP = HANDICAP
    AU = AUCTION
    CL = CLAIMER
    M = MAIDEN
    S = SELLER
    STKS = STAKES
    CLAIMING = CLAIMER
    SELLING = SELLER
    NURSERY = HANDICAP
