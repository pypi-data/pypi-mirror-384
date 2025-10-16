import pytest
from geomfig import Circle

def test_circle_area():
    c = Circle(9)
    assert abs(c.area() - 254.46900494077323) < 1e-7

def test_circle_negative_radius():
    with pytest.raises(ValueError):
        Circle(-1)

def test_circle_zero_radius():
    with pytest.raises(ValueError):
        Circle(0)