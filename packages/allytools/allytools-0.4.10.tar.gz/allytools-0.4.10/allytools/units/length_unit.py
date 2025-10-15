from enum import Enum


class LengthUnit(Enum):
    NM = (1e-9, "nm", "nanometers")
    PM = (1e-6, "pm", "picometers")
    UM = (1e-3, "µm", "micrometers")
    MM = (1.0, "mm", "millimeters")
    CM = (10.0, "cm", "centimeters")
    M = (1e3, "m", "meters")
    KM = (1e6, "km", "kilometers")

    def __init__(self, factor: float, symbol: str, fullname: str):
        self._factor = factor
        self._symbol = symbol
        self._fullname = fullname

    @property
    def factor(self) -> float:
        return self._factor

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def fullname(self) -> str:
        return self._fullname
