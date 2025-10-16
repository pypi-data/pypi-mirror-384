from .handedness import Handedness as Handedness
from .racecourse_contour import RacecourseContour as RacecourseContour
from .racecourse_shape import RacecourseShape as RacecourseShape
from .racecourse_style import RacecourseStyle as RacecourseStyle
from .surface import Surface as Surface
from _typeshed import Incomplete

class Racecourse:
    name: Incomplete
    surface: Incomplete
    handedness: Incomplete
    contour: Incomplete
    shape: Incomplete
    style: Incomplete
    def __init__(self, name: str, surface: Surface | str, **kwargs) -> None: ...
