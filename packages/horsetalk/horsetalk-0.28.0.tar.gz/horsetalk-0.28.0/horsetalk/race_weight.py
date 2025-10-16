from horsetalk.quantity import HorsetalkQuantity


class RaceWeight(HorsetalkQuantity):
    """
    A class for representing the weight carried by a horse in a race.

    """

    REGEX = r"(?:(\d+)(?:st|\-))?(?:(\d+)(?:lb)*)?"

    def __str__(self) -> str:
        """
        Returns the weight as a string.
        """
        num = self.to("lb").magnitude
        st, lb = divmod(num, 14)
        return f"{st}st {lb}lb"

    @classmethod
    def _string_arg_handler(cls, parts):
        st, lbs = parts
        return (int(st or 0) * 14 + int(lbs or 0), "lb")
