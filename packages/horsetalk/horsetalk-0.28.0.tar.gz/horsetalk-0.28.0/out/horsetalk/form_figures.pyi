from horsetalk import Disaster as Disaster, FinishingPosition as FinishingPosition, FormBreak as FormBreak

class FormFigures:
    @staticmethod
    def parse(form_figures: str) -> list[FinishingPosition | FormBreak | Disaster]: ...
