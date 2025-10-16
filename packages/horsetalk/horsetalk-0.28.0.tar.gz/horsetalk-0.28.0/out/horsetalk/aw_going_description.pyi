from .going_description import GoingDescription as GoingDescription

class AWGoingDescription(GoingDescription):
    SLOW: int
    STANDARD_TO_SLOW: int
    STANDARD: int
    STANDARD_TO_FAST: int
    FAST: int
    SLW = SLOW
    STS = STANDARD_TO_SLOW
    STD = STANDARD
    STF = STANDARD_TO_FAST
    FST = FAST
