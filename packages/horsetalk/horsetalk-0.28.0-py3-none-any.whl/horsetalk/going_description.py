from peak_utility.enumeration.parsing_enum import ParsingEnum  # type: ignore

from .surface import Surface


class GoingDescription(ParsingEnum):
    """
    A parent enumeration for more specific going descriptions. Not intended to be instantiated directly.

    """

    @property
    def surface(self):
        """
        The surface implied by the going description.

        """
        return Surface[self.__class__.__name__.replace("GoingDescription", "")]
