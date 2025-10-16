from _typeshed import Incomplete
from horsetalk.quantity import HorsetalkQuantity as HorsetalkQuantity
from horsetalk.race_distance_category import RaceDistanceCategory as RaceDistanceCategory

class RaceDistance(HorsetalkQuantity):
    POSSIBLE_DECIMAL: str
    REGEX: Incomplete
    @property
    def category(self): ...
