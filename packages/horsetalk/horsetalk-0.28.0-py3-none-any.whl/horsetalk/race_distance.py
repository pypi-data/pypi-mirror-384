from horsetalk.quantity import HorsetalkQuantity
from horsetalk.race_distance_category import RaceDistanceCategory


class RaceDistance(HorsetalkQuantity):
    """
    A convenience class for representing the distance over which a race is run.

    """

    POSSIBLE_DECIMAL = r"?:(\d+(?:\.\d+)?)"
    REGEX = rf"({POSSIBLE_DECIMAL}\s?(?:m(?:iles*)?)\s*)?({POSSIBLE_DECIMAL}\s?(?:f(?:urlongs*)?)\s*)?({POSSIBLE_DECIMAL}\s?(?:y(?:ards*)?)\s*)?"

    def __str__(self) -> str:
        """
        Returns the distance as a string.
        """
        return " ".join([
            f"{int(x)}m" if (x := self.to("mile").magnitude // 1) else "",
            f"{int(x)}f" if (x := self.to("f").magnitude % 8) else "",
            f"{int(x)}y" if (x := self.to("y").magnitude % 220) else "",
        ]).strip()

    @classmethod
    def _string_arg_handler(cls, parts):
        m, f, y = parts

        if float(m or 0) > 10:
            args = (float(m or 0), "metre")
        else:
            yards = float(m or 0) * 1760 + float(f or 0) * 220 + float(y or 0)
            args = (yards, "yard")

        return args

    @property
    def category(self):
        f = self.furlongs
        if f <= 7:
            return RaceDistanceCategory.SPRINT

        if f <= 9:
            return RaceDistanceCategory.MILE

        if f <= 13:
            return RaceDistanceCategory.MIDDLE_DISTANCE

        return RaceDistanceCategory.STAYING
