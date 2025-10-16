from .aw_going_description import AWGoingDescription
from .dirt_going_description import DirtGoingDescription
from .going_description import GoingDescription
from .surface import Surface
from .turf_going_description import TurfGoingDescription


class Going:
    """
    A class to represent a going.
    """

    Scales = (TurfGoingDescription, AWGoingDescription, DirtGoingDescription)

    def __init__(self, description: str, reading: float | None = None):
        """
        Initialize a Going instance.

        Args:
            description: The description of the going.
            reading: The reading of the going stick.
        """
        self.description = description.replace(" (", ", ").replace(")", "")
        self.reading = reading

        assert (self.primary and self.secondary) or self.primary

    def __hash__(self):
        """
        The hash of the going.

        Returns:
            The hash of the going.
        """
        return hash((self.primary, self.secondary, self.reading))

    def __repr__(self):
        """
        The repr of the going.

        Returns:
            The repr of the going.
        """
        return f"<Going({self.primary!r}, {self.secondary!r})>"

    def __str__(self):
        """
        The string representation of the going.

        Returns:
            The string representation of the going.
        """
        primary_str = self.primary.name.title()
        secondary_str = self.secondary.name.title() if self.secondary else ""
        return f"{primary_str}{', ' + secondary_str + ' in places' if secondary_str else ''}".replace(
            "_", " "
        ).replace(" To", " to")

    def __eq__(self, other: object) -> bool:
        """
        Determine if two goings are equal.

        Args:
            other: The other going.

        Returns:
            True if the goings are equal, False otherwise.
        """

        return isinstance(other, Going) and (
            self.primary == other.primary
            and self.secondary == other.secondary
            and self.reading == other.reading
        )

    @property
    def primary(self) -> GoingDescription:
        """
        The primary property of the going.

        Returns:
            A value selected from the appropriate going scale.
        """
        key = self._description_parts[0]
        return Going._lookup(key)

    @property
    def secondary(self) -> GoingDescription | None:
        """
        The secondary or 'in places' property of the going.

        Returns:
            A value selected from the appropriate going scale.
        """
        key = self._description_parts[1]
        return Going._lookup(key) if key else None

    @property
    def surface(self) -> Surface:
        """
        The surface implied by the going description.

        Returns:
            The Surface enum member implied by the going description.
        """
        return self.primary.surface

    @property
    def value(self) -> float:
        """
        A numerical value for the going.

        Returns:
            The value of the going.
        """
        return (
            self.primary.value
            if self.secondary is None
            else (self.primary.value + self.secondary.value) / 2
        )

    @property
    def _description_parts(self) -> list[str]:
        """
        The parts of the description.

        Returns:
            The parts of the description.
        """
        texts = self.description.upper().replace(" IN PLACES", "").split(", ")

        if len(texts) == 2:
            if texts[0] == texts[1]:
                raise ValueError("Primary and secondary going description cannot match")
            return texts

        return [*texts, ""]

    @classmethod
    def _lookup(cls, key: str) -> GoingDescription:
        """
        Lookup a value in the appropriate going scale.

        Args:
            key: The key to lookup.

        Returns:
            A value selected from the appropriate going scale.

        Raises:
            ValueError: If the key is not found in any of the going scales.
        """
        for scale in Going.Scales:
            try:
                return scale[key]  # type: ignore
            except KeyError:
                pass

        raise ValueError(f"Unknown going description: {key}")

    @staticmethod
    def multiparse(description: str) -> dict[str, "Going"]:
        """
        Sometimes goings are given for multiple courses, e.g. turf and all weather, chase and hurdle in the same string.
        This will parse these into a dict of Going objects, keyed by an identifier for each course

        Args:
            going: The going string to parse.

        Returns:
            A dict of Going objects.
        """
        opposites = {
            "hurdle": "chase",
            "chase": "hurdle",
            "inner": "outer",
            "outer": "inner",
            "old": "new",
            "new": "old",
            "straight": "round",
            "round": "straight",
            "flat": "aw",
            "aw": "flat",
        }

        if not any(x in description.lower() for x in opposites):
            return {"default": Going(description)}

        clauses = (
            description.lower()
            .replace(")", "")
            .replace("(", ",")
            .replace("hurdles", "hurdle")
            .split(",")
        )
        for i, clause in enumerate(clauses):
            if not any(x in clause for x in opposites) and "in places" in clause:
                clauses[i - 1] = clauses[i - 1].strip() + ", " + clause
                clauses[i] = ""
        clauses = [x for x in clauses if x]

        identifier = next(x for x in opposites if x in description.lower())

        def strip_clause(x, y):
            return (
                x.replace("on", "")
                .replace("course", "")
                .replace(":", "")
                .replace(y, "")
                .strip()
            )

        def reconstructed_going_description(identifier: str, clauses: list[str]) -> str:
            containing_clause = next((x for x in clauses if identifier in x), "")
            return (
                f"{clauses[0]}, {strip_clause(containing_clause, identifier)} in places"
                if "in places" in containing_clause and "," not in containing_clause
                else strip_clause(containing_clause, identifier)
                if containing_clause
                else clauses[0]
            )

        return {
            i: Going(reconstructed_going_description(i, clauses))
            for i in [identifier, opposites[identifier]]
        }
