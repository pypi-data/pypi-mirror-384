from dataclasses import dataclass

from pendulum import DateTime

from .going import Going
from .race_designation import RaceDesignation
from .race_distance import RaceDistance
from .race_level import RaceLevel
from .racecourse import Racecourse
from .stalls_position import StallsPosition


@dataclass(kw_only=True, frozen=True)
class RaceConditions:
    """
    A class for grouping together race conditions into a single object.

    Properties:
        datetime: The datetime of the race
        racecourse: The racecourse on which the race is run
        distance: The race distance
        going: The going of the race
        race_designation: The designation of the race, i.e. whether it is a handicap, maiden, etc.
        race_level: The level of the race, i.e. Group 1, Group 2, etc.
        stalls_position: The position of the stalls on the track

    """

    datetime: DateTime | None = None
    racecourse: Racecourse | None = None
    distance: RaceDistance | None = None
    going: Going | None = None
    race_designation: RaceDesignation | None = None
    race_level: RaceLevel | None = None
    stalls_position: StallsPosition | None = None

    def __repr__(self):
        return (
            f"<RaceConditions: datetime={self.datetime}, "
            f"racecourse={self.racecourse!r}, "
            f"distance={self.distance!s}, "
            f"going={self.going}, "
            f"race_designation={self.race_designation.name.title()}, "
            f"race_level={self.race_level.grade or self.race_level.class_}, "
            f"stalls_position={self.stalls_position}>"
        )

    def __str__(self):
        return (
            f"{self.datetime.format('D MMM YYYY, HH:mm')}, "
            f"{self.racecourse.name}, "
            f"{self.distance!s} ({self.going}), "
            f"{self.race_designation.name.title()} "
            f"{self.race_level}"
            f"{', Stalls: ' + str(self.stalls_position.name.title()) if self.stalls_position else ''}"
        )
