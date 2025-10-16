import re
from types import MappingProxyType

from peak_utility.number import RepresentationalInt  # type: ignore

from .racing_code import RacingCode


class RaceGrade(RepresentationalInt):
    """
    A class representing the grade of a race.

    """

    REGEX = r"G(?:roup|rade|)\s*"
    PHRASES = MappingProxyType({
        RacingCode.FLAT: "group",
        RacingCode.NATIONAL_HUNT: "grade",
    })

    def __new__(cls, grade: str | int | None, racing_code: RacingCode | None = None):
        """
        Create a RaceGrade instance.

        Args:
            grade: The grade to initialize with
            racing_code: The racing code to initialize with

        Raises:
            ValueError: If the grade is not valid

        """
        grade_text = re.sub(RaceGrade.REGEX, "", str(grade or "").title())

        if grade_text.isdigit() and 1 <= int(grade_text) < 4:
            grade_value = int(grade_text)
        elif grade_text == "Listed":
            grade_value = 4
        elif int(bool(grade_text)) == 0:
            grade_value = 5
        else:
            raise ValueError(f"{grade} is not a valid RaceGrade")

        code_from_grade = {v: k for k, v in RaceGrade.PHRASES.items()}.get(
            next(
                (x for x in ["grade", "group"] if x in str(grade).lower()),
                "default",
            ),
            None,
        )

        if code_from_grade and racing_code and code_from_grade != racing_code:
            raise ValueError(
                f"{grade} conflicts with value for racing code: {racing_code.value}"
            )

        instance = super().__new__(cls, grade_value)
        instance.racing_code = code_from_grade or racing_code or RacingCode.FLAT
        return instance

    def __repr__(self):
        return f"<RaceGrade: {str(int(self)) if int(self) < 4 else str(self) or 'Ungraded'}>"

    def __str__(self):
        if super().__eq__(5):
            return ""
        if super().__eq__(4):
            return "Listed"

        return (
            f"{RaceGrade.PHRASES.get(self.racing_code, 'group').title()} {int(self)!s}"
        )

    def __bool__(self):
        return super().__ne__(5)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, RaceGrade) or (
            isinstance(other, int)
            and other < 4
            and not isinstance(other, RepresentationalInt)
        ):
            return super().__eq__(other)

        return False

    def __ne__(self, other):
        if isinstance(other, RaceGrade) or (
            isinstance(other, int)
            and other < 4
            and not isinstance(other, RepresentationalInt)
        ):
            return super().__ne__(other)

        return True

    def __lt__(self, other):
        return super().__gt__(other)

    def __gt__(self, other):
        return super().__lt__(other)
