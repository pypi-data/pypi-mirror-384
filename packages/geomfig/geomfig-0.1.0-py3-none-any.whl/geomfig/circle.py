from math import pi
from .base import Figure

class Circle(Figure):
    def __init__(self, radius: float):
        if radius <= 0:
            raise ValueError("Radius must be positive")
        self.radius = radius

    def area(self) -> float:
        return pi*self.radius**2