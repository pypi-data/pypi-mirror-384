import pendulum
from .breed import Breed as Breed
from .country import Country as Country
from .hemisphere import Hemisphere as Hemisphere
from .horse_age import HorseAge as HorseAge
from _typeshed import Incomplete
from typing import NotRequired, TypedDict

class HorseAgeKwargs(TypedDict):
    context_date: pendulum.Date
    hemisphere: NotRequired[Hemisphere]

class Horse:
    REGEX: Incomplete
    name: Incomplete
    breed: Incomplete
    country: Incomplete
    age: HorseAge | None
    def __init__(self, name: str, country: Country | str | None = None, age_or_yob: int | None = None, *, context_date: pendulum.Date | None = None) -> None: ...
