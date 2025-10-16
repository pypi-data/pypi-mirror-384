from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore


class Disaster(ParsingEnum):
    """
    An enumeration representing the reason for a horse's non-completion of a race
    """

    FELL = 1
    REFUSED = 2
    BROUGHT_DOWN = 3
    UNSEATED_RIDER = 4
    PULLED_UP = 5
    SLIPPED_UP = 6
    CARRIED_OUT = 7
    RAN_OUT = 8
    LEFT_AT_START = 9
    HIT_RAIL = 10
    DISQUALIFIED = 11
    REFUSED_TO_RACE = 12

    # Abbreviations
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
    def is_jumping_error(self):
        return self in [self.FELL, self.UNSEATED_RIDER]

    @property
    def is_behavioural_error(self):
        return self in [self.REFUSED, self.RAN_OUT, self.REFUSED_TO_RACE]

    @property
    def is_third_party_error(self):
        return self in [self.BROUGHT_DOWN, self.CARRIED_OUT]
