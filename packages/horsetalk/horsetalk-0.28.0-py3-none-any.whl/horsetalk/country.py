from enum import Enum

from .hemisphere import Hemisphere


class Country(Enum):
    """
    An enumeration representing a country.

    """

    def __new__(cls, country_name, hemisphere):
        obj = object.__new__(cls)
        obj._value_ = country_name
        obj.hemisphere = hemisphere
        return obj

    ARG = ("Argentina", Hemisphere.SOUTH)
    AUS = ("Australia", Hemisphere.SOUTH)
    AUT = ("Austria", Hemisphere.NORTH)
    AZE = ("Azerbaijan", Hemisphere.NORTH)
    BHR = ("Bahrain", Hemisphere.NORTH)
    BAR = ("Barbados", Hemisphere.NORTH)
    BEL = ("Belgium", Hemisphere.NORTH)
    BOS = ("Bosnia", Hemisphere.NORTH)
    BRZ = ("Brazil", Hemisphere.SOUTH)
    BUL = ("Bulgaria", Hemisphere.NORTH)
    CAN = ("Canada", Hemisphere.NORTH)
    CHI = ("Chile", Hemisphere.SOUTH)
    CHN = ("China", Hemisphere.NORTH)
    COL = ("Colombia", Hemisphere.SOUTH)
    CRO = ("Croatia", Hemisphere.NORTH)
    CYP = ("Cyprus", Hemisphere.NORTH)
    CZE = ("Czech Republic", Hemisphere.NORTH)
    DEN = ("Denmark", Hemisphere.NORTH)
    DOM = ("Dominican Republic", Hemisphere.NORTH)
    ECU = ("Ecuador", Hemisphere.SOUTH)
    FIN = ("Finland", Hemisphere.NORTH)
    FR = ("France", Hemisphere.NORTH)
    GER = ("Germany", Hemisphere.NORTH)
    GB = ("Great Britain", Hemisphere.NORTH)
    GR = ("Greece", Hemisphere.NORTH)
    HER = ("Herzegovina", Hemisphere.NORTH)
    HUN = ("Hungary", Hemisphere.NORTH)
    IND = ("India", Hemisphere.NORTH)
    IRE = ("Ireland", Hemisphere.NORTH)
    IRN = ("Iran", Hemisphere.NORTH)
    ITY = ("Italy", Hemisphere.NORTH)
    JAM = ("Jamaica", Hemisphere.NORTH)
    JPN = ("Japan", Hemisphere.NORTH)
    KEN = ("Kenya", Hemisphere.NORTH)
    KOR = ("Korea", Hemisphere.NORTH)
    LEB = ("Lebanon", Hemisphere.NORTH)
    LTU = ("Lithuania", Hemisphere.NORTH)
    LUX = ("Luxembourg", Hemisphere.NORTH)
    MAL = ("Malaysia", Hemisphere.NORTH)
    MEX = ("Mexico", Hemisphere.NORTH)
    MOR = ("Morocco", Hemisphere.NORTH)
    HOL = ("Netherlands", Hemisphere.NORTH)
    NZ = ("New Zealand", Hemisphere.SOUTH)
    NOR = ("Norway", Hemisphere.NORTH)
    OM = ("Oman", Hemisphere.NORTH)
    PAK = ("Pakistan", Hemisphere.NORTH)
    PRY = ("Paraguay", Hemisphere.SOUTH)
    PER = ("Peru", Hemisphere.SOUTH)
    PHI = ("Philippines", Hemisphere.NORTH)
    POL = ("Poland", Hemisphere.NORTH)
    POR = ("Portugal", Hemisphere.NORTH)
    PR = ("Puerto Rico", Hemisphere.NORTH)
    QA = ("Qatar", Hemisphere.NORTH)
    RUM = ("Romania", Hemisphere.NORTH)
    RUS = ("Russia", Hemisphere.NORTH)
    KSA = ("Saudi Arabia", Hemisphere.NORTH)
    SER = ("Serbia", Hemisphere.NORTH)
    SVK = ("Slovakia", Hemisphere.NORTH)
    SVN = ("Slovenia", Hemisphere.NORTH)
    SAF = ("South Africa", Hemisphere.SOUTH)
    SPA = ("Spain", Hemisphere.NORTH)
    SWE = ("Sweden", Hemisphere.NORTH)
    SWI = ("Switzerland", Hemisphere.NORTH)
    SY = ("Syria", Hemisphere.NORTH)
    TRI = ("Trinidad and Tobago", Hemisphere.NORTH)
    TUN = ("Tunisia", Hemisphere.NORTH)
    TUR = ("Turkey", Hemisphere.NORTH)
    UAE = ("United Arab Emirates", Hemisphere.NORTH)
    USA = ("United States of America", Hemisphere.NORTH)
    URU = ("Uruguay", Hemisphere.SOUTH)
    UZB = ("Uzbekistan", Hemisphere.NORTH)
    VEN = ("Venezuela", Hemisphere.NORTH)
    ZIM = ("Zimbabwe", Hemisphere.SOUTH)

    def __str__(self):
        return self.value
