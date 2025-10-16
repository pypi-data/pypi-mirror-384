import pendulum

from .disaster import Disaster
from .finishing_position import FinishingPosition
from .horselength import Horselength
from .outcome import Outcome


class RacePerformance:
    """
    A class for grouping together race performance stats into a single object.

    """

    def __init__(
        self,
        outcome: str | int | Disaster | FinishingPosition | Outcome,
        *,
        official_position: str | int | FinishingPosition | None = None,
        beaten_distance: str | int | Horselength | None = None,
        time: pendulum.Duration | None = None,
        comments: str | None = None,
    ):
        """
        Initialize a RacePerformance instance.

        Args:
            outcome: A disaster or finishing position
            official_position: The official finishing position
            beaten_distance: The beaten distance
            comments: Race comments on this performance

        Raises:
            ValueError: If both a disaster and a finishing position are given

        """
        self.comments = comments
        self.outcome = Outcome(outcome) if not isinstance(outcome, Outcome) else outcome
        self.official_position = (
            Outcome(official_position)
            if official_position
            else self.outcome
            if self.outcome.is_completion
            else None
        )
        self.beaten_distance = (
            None if beaten_distance is None else Horselength(beaten_distance)
        )
        self.time = time

        if not self.is_completion:
            if self.official_position:
                raise ValueError(
                    f"Cannot have both a disaster {self.outcome} and a position {self.official_position}"
                )
            if self.beaten_distance:
                raise ValueError(
                    f"Cannot have both a disaster {self.outcome} and a beaten distance {self.beaten_distance}"
                )

    def __repr__(self):
        official_position_repr = (
            f", placed {int(self.official_position._value)}"
            if self.official_position and self.official_position != self.outcome
            else ""
        )
        return f"<RacePerformance: {(int if self.is_completion else str)(self.outcome._value)}{official_position_repr}>"

    def __str__(self):
        official_position_str = (
            f", placed {self.official_position}"
            if self.official_position and self.official_position != self.outcome
            else ""
        )
        return f"{self.outcome}{official_position_str}"

    def __lt__(self, other):
        if not isinstance(other, RacePerformance):
            return NotImplemented
        return self.outcome < other.outcome

    @property
    def is_completion(self) -> bool:
        return self.outcome.is_completion

    @property
    def is_official_win(self) -> bool:
        return (
            self.is_completion
            and self.official_position is not None
            and self.official_position.is_win
        )

    @property
    def is_win(self) -> bool:
        return self.outcome.is_win
