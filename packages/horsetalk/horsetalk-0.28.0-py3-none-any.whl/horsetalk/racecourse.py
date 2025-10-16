from .handedness import Handedness
from .racecourse_contour import RacecourseContour
from .racecourse_shape import RacecourseShape
from .racecourse_style import RacecourseStyle
from .surface import Surface


class Racecourse:
    """
    A class for grouping together racecourse characteristics into a single object.

    """

    def __init__(self, name: str, surface: Surface | str, **kwargs):
        """
        Initialize a Racecourse instance.

        Args:
            name: The name of the racecourse
            surface: The surface on which the racecourse is run
            handedness: The handedness of the racecourse
            contour: The contour of the racecourse
            shape: The shape of the racecourse
            style: The style of the racecourse

        """
        handedness = kwargs.get("handedness", "unknown")
        contour = kwargs.get("contour", "unknown")
        shape = kwargs.get("shape", "unknown")
        style = kwargs.get("style", "unknown")

        self.name = name
        self.surface = Surface[surface] if isinstance(surface, str) else surface  # type: ignore
        self.handedness = (
            Handedness[handedness] if isinstance(handedness, str) else handedness  # type: ignore
        )
        self.contour = (
            RacecourseContour[contour] if isinstance(contour, str) else contour  # type: ignore
        )
        self.shape = RacecourseShape[shape] if isinstance(shape, str) else shape  # type: ignore
        self.style = RacecourseStyle[style] if isinstance(style, str) else style  # type: ignore

    def __repr__(self):
        return f"<Racecourse: {self.name}, {self.surface}>"

    def __str__(self):
        return f"{self.name} ({self.surface.name.title()})"
