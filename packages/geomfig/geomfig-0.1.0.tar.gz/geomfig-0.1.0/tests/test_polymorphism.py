from geomfig import Circle, Triangle, Figure

def compute_total_area(figure: list[Figure]):
    return sum([fig.area() for fig in figure])

def test_polymorphism():
    ls_fig = [Circle(3), Triangle(3, 4, 5)]
    assert abs(compute_total_area(ls_fig) - 34.27433388230814) < 1e-7