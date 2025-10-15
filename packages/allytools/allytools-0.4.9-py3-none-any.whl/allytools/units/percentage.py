from dataclasses import dataclass


@dataclass(frozen=True)
class Percentage:
    value: float

    def as_fraction(self) -> float:
        return self.value / 100.0

    def __str__(self):
        return f"{self.value:.2f}%"
