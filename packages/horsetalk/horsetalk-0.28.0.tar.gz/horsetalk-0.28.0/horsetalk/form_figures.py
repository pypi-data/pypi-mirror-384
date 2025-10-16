from horsetalk import Disaster, FinishingPosition, FormBreak


class FormFigures:
    """
    A class to parse a string of form figures into a list of corresponding objects.

    Methods:
        parse:
            Parses the given string of form figures and returns a list of corresponding objects.

    """

    @staticmethod
    def parse(form_figures: str) -> list[FinishingPosition | FormBreak | Disaster]:
        """
        Parses the given string of form figures and returns a list of corresponding objects.
        Each form figure is converted to a corresponding object based on its value, where:
            - If the figure is a digit, it is converted to a FinishingPosition object.
            - If the figure is a valid FormBreak value, it is converted to a FormBreak object.
            - If the figure is a valid Disaster value, it is converted to a Disaster object.

        Args:
            form_figures: The string of form figures to parse.

        Returns:
            A list of objects representing the form figures.

        Raises:
            None

        """
        return [
            FinishingPosition(figure)
            if figure.isdigit()
            else FormBreak(figure)
            if figure in [member.value for member in FormBreak]
            else Disaster[figure]  # type: ignore
            for figure in form_figures
        ]
