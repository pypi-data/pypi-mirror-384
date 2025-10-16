from .race_class import RaceClass
from .race_grade import RaceGrade


class RaceLevel:
    """
    A class representing the level of the race.

    """

    def __init__(self, value: str | RaceGrade | RaceClass):
        """
        Initialize a RaceLevel instance.

        Args:
            value: The value to initialize with

        Raises:
            ValueError: if Class 1 is given, but no grade is specified

        """
        if isinstance(value, RaceClass) and value == 1:
            raise ValueError("Class 1 race needs a specified grade")

        self.grade = (
            value
            if isinstance(value, RaceGrade)
            else RaceGrade(
                value if "G" in str(value) or str(value).lower() == "listed" else None
            )
        )
        self.class_ = (
            value
            if isinstance(value, RaceClass)
            else RaceClass(1)
            if self.grade
            else RaceClass(value)
        )

    def __repr__(self):
        return f"<RaceLevel: {repr(self.grade) if self.grade else repr(self.class_)}>"

    def __str__(self):
        return f"({int(self.class_)}) {self.grade}".strip()

    def __hash__(self):
        return hash((self.grade, self.class_))

    def __eq__(self, other):
        return self.grade == other.grade and self.class_ == other.class_

    def __gt__(self, other):
        return self.grade > other.grade or self.class_ > other.class_

    def __lt__(self, other):
        return self.grade < other.grade or self.class_ < other.class_
