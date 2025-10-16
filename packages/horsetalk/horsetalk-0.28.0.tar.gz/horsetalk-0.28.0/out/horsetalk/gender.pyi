from .sex import Sex as Sex
from peak_utility.enumeration.parsing_enum import ParsingEnum

class Gender(ParsingEnum):
    FOAL: int
    YEARLING: int
    COLT: int
    FILLY: int
    STALLION: int
    MARE: int
    GELDING: int
    RIG: int
    ENTIRE: int
    HORSE: int
    C = COLT
    F = FILLY
    S = STALLION
    M = MARE
    G = GELDING
    R = RIG
    E = ENTIRE
    H = HORSE
    FOALS = FOAL
    YEARLINGS = YEARLING
    COLTS = COLT
    FILLIES = FILLY
    STALLIONS = STALLION
    MARES = MARE
    GELDINGS = GELDING
    RIGS = RIG
    ENTIRES = ENTIRE
    HORSES = HORSE
    @property
    def sex(self): ...
    @property
    def has_testes(self): ...
    @staticmethod
    def determine(official_age: int, sex: Sex | None = None, **kwargs): ...
