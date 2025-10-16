from math import sqrt
from .base import Figure

class Triangle(Figure):
    def __init__(self, s1: float, s2: float, s3: float):
        if s1 <= 0 or s2 <= 0 or s3 <= 0:
            raise ValueError("All sides must be positive")
        # Проверка неравенства треугольника
        if s1 + s2 <= s3 or s1 + s3 <= s2 or s2 + s3 <= s1:
            raise ValueError("Invalid triangle sides")
        self.s1, self.s2, self.s3 = s1, s2, s3

    def area(self) -> float:
        ls = sorted([self.s1, self.s2, self.s3], reverse=False)
        #проверка на прямоугольный треугольник
        if (abs(ls[0]**2+ls[1]**2-ls[2]**2) < 1e-7):
            return (ls[0]*ls[1])/2
        else:# Формула Герона
            p = (self.s1 + self.s2 + self.s3)/2
            return sqrt(p*(p-self.s1)*(p-self.s2)*(p-self.s3))
