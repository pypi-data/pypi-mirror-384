import re


class AgeRestriction:
    REGEX = (
        r"(\d{1,2})[-]?(\d{1,2})?\s?y(?:ear)?(?:\s|-)?o(?:ld(?:s)?)?(?:\sonly)?(\+)?"
    )

    def __init__(self, string: str | None):
        """
        Initialize an AgeRestriction instance.

        Args:
            age_restriction_string: The age restriction string.

        Returns:
            An AgeRestriction instance.
        """
        if not string or not (matches := re.search(self.REGEX, string)):
            self.minimum = None
            self.maximum = None
        else:
            groups = matches.groups()
            mini, maxi, plus = list(groups) + [None] * (3 - len(groups))

            self.minimum = int(mini)
            self.maximum = None if plus else int(maxi or mini)

    def __repr__(self):
        """
        Returns the age restriction as a repr.

        Returns:
            The age restriction as a repr.
        """
        return f"<AgeRestriction: {self!s}>"

    def __str__(self):
        """
        Returns the age restriction as a string.

        Returns:
            The age restriction as a string.
        """
        if self.minimum == self.maximum:
            return f"{self.minimum}yo"

        if self.maximum:
            return f"{self.minimum}-{self.maximum}yo"

        return f"{self.minimum}yo+"
