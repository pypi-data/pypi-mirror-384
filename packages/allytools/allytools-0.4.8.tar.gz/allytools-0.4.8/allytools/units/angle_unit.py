from enum import Enum
from math import pi


class AngleUnit(Enum):
    DEG = (1.0, "°", "degrees")
    RAD = (180.0 / pi, "rad", "radians")
    MRAD = (0.180 / pi, "mrad", "milliradians")

    def __init__(self, factor: float, symbol: str, fullname: str):
        self._factor = factor  # how many degrees in 1 unit
        self._symbol = symbol
        self._fullname = fullname

    @property
    def factor(self) -> float:
        """Conversion factor to degrees."""
        return self._factor

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def fullname(self) -> str:
        return self._fullname

    def __str__(self) -> str:
        return self.symbol
