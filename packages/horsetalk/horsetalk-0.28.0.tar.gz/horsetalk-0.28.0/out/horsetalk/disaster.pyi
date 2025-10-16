from peak_utility.enumeration.parsing_enum import ParsingEnum

class Disaster(ParsingEnum):
    FELL: int
    REFUSED: int
    BROUGHT_DOWN: int
    UNSEATED_RIDER: int
    PULLED_UP: int
    SLIPPED_UP: int
    CARRIED_OUT: int
    RAN_OUT: int
    LEFT_AT_START: int
    HIT_RAIL: int
    DISQUALIFIED: int
    REFUSED_TO_RACE: int
    F = FELL
    R = REFUSED
    REF = REFUSED
    B = BROUGHT_DOWN
    BD = BROUGHT_DOWN
    U = UNSEATED_RIDER
    UR = UNSEATED_RIDER
    P = PULLED_UP
    PU = PULLED_UP
    S = SLIPPED_UP
    SU = SLIPPED_UP
    C = CARRIED_OUT
    CO = CARRIED_OUT
    O = RAN_OUT
    RO = RAN_OUT
    L = LEFT_AT_START
    LEFT = LEFT_AT_START
    HR = HIT_RAIL
    D = DISQUALIFIED
    DQ = DISQUALIFIED
    DSQ = DISQUALIFIED
    RR = REFUSED_TO_RACE
    @property
    def is_jumping_error(self): ...
    @property
    def is_behavioural_error(self): ...
    @property
    def is_third_party_error(self): ...
