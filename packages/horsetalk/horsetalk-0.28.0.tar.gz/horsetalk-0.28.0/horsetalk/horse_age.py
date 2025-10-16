from typing import Self

import pendulum
from pendulum import Date, Interval

from .hemisphere import Hemisphere


class HorseAge:
    """
    A class representing the age of a horse.

    Attributes:
        _official_dob (Date): The official date of birth of the horse.
        _actual_dob (Date): The actual date of birth of the horse.
        _context_date (Date): The context date for calculating the age of the horse.

    """

    def __init__(
        self,
        official_age: int | None = None,
        *,
        foaling_date: Date | None = None,
        birth_year: int | None = None,
        context_date: Date | None = None,
        hemisphere: Hemisphere = Hemisphere(1),
    ):
        """
        Initializes a new instance of the HorseAge class with the specified parameters.
        If official_age and either foaling_date or birth_year are both provided, a ValueError is raised.
        If no arguments are provided, a ValueError is raised.

        Args:
            official_age (int | None): The official age of the horse.
            foaling_date (Date | None): The actual date of birth of the horse.
            birth_year (int | None): The birth year of the horse.
            context_date (Date | None): The context date for calculating the age of the horse.
            hemisphere (Hemisphere): The hemisphere where the horse was born. This is used to
                determine the horse's age based on the hemisphere-specific
                standard. The default is Hemisphere.NORTHERN.

        Returns:
            None

        Raises:
            ValueError: If invalid arguments are provided.

        """
        if official_age is not None and (foaling_date or birth_year):
            raise ValueError(
                "Cannot initialize HorseAge with both official_age and keyword"
            )

        if not (official_age or foaling_date or birth_year):
            raise ValueError(
                "Cannot initialize HorseAge without official_age, foaling_date, or birth_year"
            )

        self._actual_dob = foaling_date
        self._context_date = context_date

        year = birth_year or (
            self._base_date.year - official_age
            if official_age
            else foaling_date.year
            if foaling_date
            else None
        )

        assert year

        official_birth_month = 1 if hemisphere == Hemisphere.NORTHERN else 8

        known_born_before_august = foaling_date and foaling_date.month < 8
        current_date_before_august = self._base_date.month < 8
        year_adjustment = int(
            bool(
                hemisphere == Hemisphere.SOUTHERN
                and (
                    known_born_before_august
                    or (not foaling_date and current_date_before_august)
                )
            )
        )

        self._official_dob = pendulum.date(
            year - year_adjustment, official_birth_month, 1
        )

    def __repr__(self) -> str:
        """
        Returns:
            A representation of the HorseAge object.
        """
        dob_repr = (
            self._actual_dob.format("D/M/YYYY") if self._actual_dob else "unknown dob"
        )
        return f"<HorseAge: {self.official.years} ({dob_repr})>"

    def __str__(self) -> str:
        """
        Returns:
            A string representation of the HorseAge object.
        """
        return str(self.official.years)

    @property
    def official(self) -> Interval:
        """
        Calculate the official age of the horse based on its birth year or foaling date.

        Raises:
            ValueError: if the official date of birth is unknown

        Returns:
            A Interval object representing the horse's official age in years, months, and days.
        """
        return self._calc_age(self._official_dob)

    @property
    def actual(self) -> Interval:
        """
        Calculate the actual age of the horse based on its actual date of birth.

        Raises:
            ValueError: if the actual date of birth is unknown

        Returns:
            A Interval object representing the horse's actual age in years, months, and days.
        """
        if not self._actual_dob:
            raise ValueError("Cannot calculate actual age as actual dob is unknown")
        return self._calc_age(self._actual_dob)

    @property
    def date_of_birth(self) -> Date:
        """
        Get the date of birth of the horse.

        Returns:
            A Date object representing the date of birth of the horse.
        """
        if not self._actual_dob:
            raise ValueError("Actual dob is unknown")
        return self._actual_dob

    @property
    def year_of_birth(self) -> int:
        """
        Get the year of birth of the horse.

        Returns:
            An integer representing the year of birth of the horse.
        """
        return self._official_dob.year

    @property
    def _base_date(self) -> Date:
        """
        Get the base date for calculating the age of the horse.

        Returns:
            A Date object representing the current date if the context date is not set,
            otherwise the context date.
        """
        return self._context_date or pendulum.today().date()

    def at(self, date: Date) -> Self:
        """
        Set the context date for calculating the age of the horse.

        Args:
            date: A Date object representing the date to set the context to.

        Returns:
            A HorseAge object with the context date set.
        """
        self._context_date = date
        return self

    def _calc_age(self, dob: Date) -> Interval:
        """
        Calculate the age of the horse based on its date of birth.

        Args:
            dob: A Date object representing the date of birth of the horse.

        Returns:
            A Interval object representing the age of the horse in years, months, and days.
        """
        return max(self._base_date - dob, self._base_date - self._base_date)
