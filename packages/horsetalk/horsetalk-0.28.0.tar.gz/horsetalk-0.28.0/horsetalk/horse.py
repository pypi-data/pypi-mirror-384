import re
from typing import NotRequired, TypedDict

import pendulum

from .breed import Breed
from .country import Country
from .hemisphere import Hemisphere
from .horse_age import HorseAge


class HorseAgeKwargs(TypedDict):
    context_date: pendulum.Date
    hemisphere: NotRequired[Hemisphere]


class Horse:
    """A class used to represent a Horse.

    Attributes:
        name (str): The name of the horse.
        breed (Breed): The breed of the horse.
        country (str): The country where the horse was bred.
        age (HorseAge | None): The age of the horse.

    Args:
        name (str): The name of the horse.
        country (str, optional): The country where the horse was bred. Defaults to None.
        age_or_yob (int, optional): The age or year of birth of the horse. Defaults to None.
        context_date (date, optional): The context date used to calculate the age of the horse. Defaults to current date.
    """

    REGEX = re.compile(
        r"""
        (?P<name>[A-Za-z]{1}[A-Za-z ']{1,19}[A-Za-z]{1})            # Horse's name
        \s*                                                         # Optional whitespace
        (?:\((?P<country>\w+)\))?                                   # Country of origin
        \s*                                                         # Optional whitespace
        (?P<age_or_yob>\d{1,4})?                                    # Age or year of birth
    """,
        re.VERBOSE,
    )

    def __init__(
        self,
        name: str,
        country: Country | str | None = None,
        age_or_yob: int | None = None,
        *,
        context_date: pendulum.Date | None = None,
    ):
        """Initializes the Horse object with name, country, age_or_yob, and context_date.

        Args:
            name (str): The name of the horse.
            country (str, optional): The country where the horse was bred. Defaults to None.
            age_or_yob (int, optional): The age or year of birth of the horse. Defaults to None.
            context_date (date, optional): The context date used to calculate the age of the horse. Defaults to current date.
        """
        match = re.match(Horse.REGEX, name)

        if not match:
            raise ValueError(f"Invalid horse name: {name}")

        if not context_date:
            context_date = pendulum.today().date()

        self.name = match.group("name")
        self.breed = None if len(self.name) <= 18 else Breed.AQPS
        self.country = (
            Country[str(key)] if (key := match.group("country") or country) else None
        )
        self.age: HorseAge | None = None

        if country and Country[str(country)] != self.country:
            raise ValueError(
                f"Conflicting countries in name and country arguments: {country}"
            )

        if (
            age_or_yob
            and match.group("age_or_yob")
            and int(match.group("age_or_yob")) != age_or_yob
        ):
            raise ValueError(
                f"Conflicting age_or_yob in name and age_or_yob arguments: {age_or_yob}"
            )

        age_or_yob = int(match.group("age_or_yob") or age_or_yob or -1)

        kwargs: HorseAgeKwargs = {"context_date": context_date}
        if self.country:
            kwargs["hemisphere"] = self.country.hemisphere  # type: ignore

        if age_or_yob > 999:
            self.age = HorseAge(birth_year=age_or_yob, **kwargs)
        elif age_or_yob > 0:
            self.age = HorseAge(age_or_yob, **kwargs)
