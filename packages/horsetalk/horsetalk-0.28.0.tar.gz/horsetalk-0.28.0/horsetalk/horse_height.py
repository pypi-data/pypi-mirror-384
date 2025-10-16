from horsetalk.quantity import HorsetalkQuantity


class HorseHeight(HorsetalkQuantity):
    """
    A class for measuring a horse's height.

    """

    def __str__(self) -> str:
        """
        Returns:
            A string representation of the HorseHeight object.
        """
        return f"{self.to('hh').magnitude}hh"
