from dataclasses import dataclass
from math import isinf

from allytools.units.angle_unit import AngleUnit


@dataclass(frozen=True)
class Angle:
    value_rad: float  # Always stored internally in radians
    _original_unit: AngleUnit = AngleUnit.RAD  # default unit

    @staticmethod
    def from_value(value: float, unit: AngleUnit = AngleUnit.DEG) -> "Angle":
        return Angle(value_rad=value * unit.factor, _original_unit=unit)

    def to(self, unit: AngleUnit) -> float:
        return self.value_rad / unit.factor

    def to_angle(self, unit: AngleUnit) -> "Angle":
        return Angle.from_value(self.to(unit), unit)

    @staticmethod
    def infinity() -> "Angle":
        return Angle(value_rad=float("inf"), _original_unit=AngleUnit.RAD)

    def is_infinite(self) -> bool:
        return isinf(self.value_rad)

    def original_unit(self) -> AngleUnit:
        return self._original_unit

    def __str__(self) -> str:
        return f"{self.to(self._original_unit):.2f} {self._original_unit.symbol}"

    def __add__(self, other: "Angle") -> "Angle":
        return Angle(self.value_rad + other.value_rad, self._original_unit)

    def __sub__(self, other: "Angle") -> "Angle":
        return Angle(self.value_rad - other.value_rad, self._original_unit)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Angle):
            return NotImplemented
        return abs(self.value_rad - other.value_rad) < 1e-6

    def __lt__(self, other: "Angle") -> bool:
        return self.value_rad < other.value_rad

    def __le__(self, other: "Angle") -> bool:
        return self.value_rad <= other.value_rad

    def __gt__(self, other: "Angle") -> bool:
        return self.value_rad > other.value_rad

    def __ge__(self, other: "Angle") -> bool:
        return self.value_rad >= other.value_rad

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Angle(self.value_rad * other, self._original_unit)
        raise TypeError(f"Cannot multiply Angle by object of type {type(other).__name__}")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Angle(self.value_rad / other, self._original_unit)
        raise TypeError(f"Cannot divide Angle by object of type {type(other).__name__}")

    def ratio_to(self, other: "Angle") -> float:
        if not isinstance(other, Angle):
            raise TypeError(f"Can only compare Angle to another Angle, not {type(other).__name__}")
        return self.value_rad / other.value_rad
