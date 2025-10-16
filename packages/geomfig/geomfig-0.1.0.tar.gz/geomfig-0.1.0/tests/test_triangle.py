import pytest
from geomfig import Triangle

def test_triangle_area():
    t = Triangle(6, 7, 3)
    assert abs(t.area() - 8.94427190999916) < 1e-7

#Проверка на прямоугольный  треугольник
def test_right_angle_triangle_area():
    t = Triangle(3, 4, 5)
    assert abs(t.area()-6) < 1e-7

#Проверка на отрицательную сторону
def test_triangle_negative_side():
    with pytest.raises(ValueError):
        Triangle(8, -2, 9)

#Проверка на нулевую сторону
def test_triangle_zero_side():
    with pytest.raises(ValueError):
        Triangle(3, 2, 0)

#Проверка неравнества треугольника
def test_triangle_inequality():
    with pytest.raises(ValueError):
        Triangle(3, 8, 14)