import numpy as np

from impose.geometry import shapes


def test_getstate_circle():
    shp = shapes.Circle(x=11, y=10, r=8, point_um=.25)
    assert shp.__getstate__()["x"] == 11
    assert shp.__getstate__()["y"] == 10
    assert shp.__getstate__()["r"] == 8
    assert shp.__getstate__()["point_um"] == 0.25


def test_getstate_ellipse():
    shp = shapes.Ellipse(x=11, y=10, a=8, b=9, point_um=.25)
    assert shp.__getstate__()["x"] == 11
    assert shp.__getstate__()["y"] == 10
    assert shp.__getstate__()["a"] == 8
    assert shp.__getstate__()["b"] == 9
    assert shp.__getstate__()["point_um"] == 0.25


def test_getstate_polygon():
    points = [[20, 20], [40, 50], [80, 10]]
    shp = shapes.Polygon(points=points, point_um=1)
    assert np.allclose(shp.__getstate__()["points"], points)
    assert shp.__getstate__()["point_um"] == 1


def test_getstate_rectangle():
    shp = shapes.Rectangle(x=11, y=10, a=8, b=9, point_um=.25)
    assert shp.__getstate__()["x"] == 11
    assert shp.__getstate__()["y"] == 10
    assert shp.__getstate__()["a"] == 8
    assert shp.__getstate__()["b"] == 9
    assert shp.__getstate__()["point_um"] == 0.25


def test_rotate_circle():
    shp = shapes.Circle(x=11, y=10, r=8, point_um=.25)
    mask1 = shp.to_mask(shape=(20, 20))
    shp.rotate(dphi=np.pi/2)
    assert shp.phi == np.pi/2
    mask2 = shp.to_mask(shape=(20, 20))
    # rotation happens around the center (x, y)
    assert np.all(mask1 == mask2)


def test_rotate_ellipse():
    shp = shapes.Ellipse(x=10, y=10, a=8, b=9, point_um=.25)
    mask1 = shp.to_mask(shape=(20, 20))
    shp.rotate(dphi=np.pi/2)
    assert shp.phi == np.pi/2
    mask2 = shp.to_mask(shape=(20, 20))
    assert np.all(mask1 == mask2.transpose())


def test_rotate_ellipse_origin():
    shp = shapes.Ellipse(x=10, y=0, a=8, b=9, point_um=.25)
    shp.rotate(dphi=np.pi/2, origin=(5, 0))
    assert shp.x == 5
    assert shp.y == 5
    assert shp.phi == np.pi/2


def test_rotate_ellipse_origin2():
    shp = shapes.Ellipse(x=6, y=5, a=8, b=9, phi=-np.pi/4, point_um=.25)
    shp.rotate(dphi=np.pi/2, origin=(1, 0))
    assert shp.x == -4
    assert shp.y == 5
    assert shp.phi == np.pi/4


def test_rotate_polygon():
    points = [[1, 1], [10, 1], [10, 10], [1, 10]]
    shp = shapes.Polygon(points=points, point_um=1)
    mask1 = shp.to_mask(shape=(20, 20))
    shp.rotate(dphi=np.pi / 2)  # rotation around mean of points
    mask2 = shp.to_mask(shape=(20, 20))
    # this works because the center of the polygon is symmetric in x and y
    assert np.all(mask1 == mask2)


def test_rotate_polygon_2():
    points = [[4, 6], [12, 6], [12, 10], [4, 10]]
    shp = shapes.Polygon(points=points, point_um=1)
    mask1 = shp.to_mask(shape=(22, 22))
    shp.rotate(dphi=np.pi / 2)  # rotation around mean of points
    mask2 = shp.to_mask(shape=(22, 22))
    # this works because the center of the polygon is symmetric in x and y
    assert np.all(mask1 == mask2.transpose())


def test_rotate_polygon_3():
    points = [[4, 8], [12, 8], [12, 10], [4, 10]]
    shp = shapes.Polygon(points=points, point_um=1)
    mask1 = shp.to_mask(shape=(22, 22))
    shp.rotate(dphi=np.pi / 2)  # rotation around mean of points
    mask2 = shp.to_mask(shape=(22, 22))
    assert shp.x == np.array(points)[:, 0].mean()
    assert shp.y == np.array(points)[:, 1].mean()
    assert not np.all(mask1 == mask2.transpose())


def test_rotate_polygon_origin():
    points = [[2, 2], [4, 2], [3, 3]]
    shp = shapes.Polygon(points=points, point_um=1)
    shp.rotate(dphi=np.pi, origin=(1, 1))
    assert np.allclose(shp.points[0][0], 0)
    assert np.allclose(shp.points[0][1], 0)
    assert np.allclose(shp.points[1][0], -2)
    assert np.allclose(shp.points[1][1], 0)
    assert np.allclose(shp.points[2][0], -1)
    assert np.allclose(shp.points[2][1], -1)


def test_rotate_rectangle():
    shp = shapes.Rectangle(x=10, y=10, a=8, b=9, point_um=.25)
    mask1 = shp.to_mask(shape=(20, 20))
    shp.rotate(dphi=np.pi/2)
    assert shp.phi == np.pi/2
    mask2 = shp.to_mask(shape=(20, 20))
    assert np.all(mask1 == mask2.transpose())


def test_rotate_rectangle_origin():
    shp = shapes.Ellipse(x=10, y=0, a=8, b=9, point_um=.25)
    shp.rotate(dphi=np.pi/2, origin=(5, 0))
    assert shp.x == 5
    assert shp.y == 5
    assert shp.phi == np.pi/2


def test_setstate_circle():
    shp = shapes.Circle(x=11, y=10, r=8, point_um=.25)
    state = shp.__getstate__()
    state["x"] = 16
    state["point_um"] = 32
    shp.__setstate__(state)
    assert shp.x == 16
    assert shp.point_um == 32


def test_setstate_ellipse():
    shp = shapes.Ellipse(x=11, y=10, a=8, b=9, point_um=.25)
    state = shp.__getstate__()
    state["b"] = 12
    state["x"] = 16
    state["point_um"] = 32
    shp.__setstate__(state)
    assert shp.b == 12
    assert shp.x == 16
    assert shp.point_um == 32


def test_setstate_polygon():
    points = [[4, 8], [12, 8], [12, 10], [4, 10]]
    shp = shapes.Polygon(points=points, point_um=1)
    state = shp.__getstate__()
    state["points"] = np.array(points) * 2
    state["point_um"] = 32
    shp.__setstate__(state)
    assert shp.point_um == 32
    assert np.all(shp.points == np.array(points) * 2)


def test_setstate_rectangle():
    shp = shapes.Rectangle(x=11, y=10, a=8, b=9, point_um=.25)
    state = shp.__getstate__()
    state["b"] = 12
    state["x"] = 16
    state["point_um"] = 32
    shp.__setstate__(state)
    assert shp.b == 12
    assert shp.x == 16
    assert shp.point_um == 32


def test_set_scale_circle():
    shp = shapes.Circle(x=0, y=1, r=8, point_um=1)
    shp.set_scale(point_um=2)
    assert shp.x == 0
    assert shp.y == .5
    assert shp.r == 4
    assert shp.a == 4
    assert shp.b == 4
    assert shp.point_um == 2


def test_set_scale_ellipse():
    shp = shapes.Ellipse(x=0, y=1, a=8, b=9, point_um=.25)
    shp.set_scale(point_um=2)
    assert shp.x == 0
    assert shp.y == 1 / 8
    assert shp.a == 8 / 8
    assert shp.b == 9 / 8
    assert shp.point_um == 2


def test_set_scale_polygon():
    points = [[4, 8], [12, 8], [12, 10], [4, 10]]
    shp = shapes.Polygon(points=points, point_um=0.25)
    shp.set_scale(point_um=3)
    assert shp.x == np.array(points)[:, 0].mean() / 12
    assert shp.y == np.array(points)[:, 1].mean() / 12
    assert shp.point_um == 3


def test_set_scale_rectangle():
    shp = shapes.Rectangle(x=0, y=1, a=8, b=9, point_um=.25)
    shp.set_scale(point_um=2)
    assert shp.x == 0
    assert shp.y == 1 / 8
    assert shp.a == 8 / 8
    assert shp.b == 9 / 8
    assert shp.point_um == 2


def test_set_size_circle():
    shp = shapes.Circle(x=0, y=1, r=8, point_um=.25)
    shp.set_size(size_um=3.5)
    radius = 3.5 / .25 / 2  # new size is diameter, divided by point_um
    assert shp.x == 0
    assert shp.y == 1
    assert shp.r == radius
    assert shp.a == radius
    assert shp.b == radius
    assert shp.point_um == 0.25


def test_set_size_ellipse():
    shp = shapes.Ellipse(x=0, y=1, a=8, b=9, point_um=.25)
    shp.set_size(size_um=3.5)
    b_new = 3.5 / .25 / 2  # new size is diameter, divided by point_um
    assert shp.x == 0
    assert shp.y == 1
    assert shp.a == b_new / 9 * 8  # relative
    assert shp.b == b_new
    assert shp.point_um == 0.25


def test_set_size_ellipse_2():
    shp = shapes.Ellipse(x=0, y=1, a=10, b=9, point_um=.25)
    shp.set_size(size_um=3.5)
    a_new = 3.5 / .25 / 2  # new size is diameter, divided by point_um
    assert shp.x == 0
    assert shp.y == 1
    assert shp.a == a_new
    assert shp.b == a_new / 10 * 9  # relative
    assert shp.point_um == 0.25


def test_set_size_polygon():
    points = [[4, 8], [12, 8], [12, 10], [4, 10]]
    shp = shapes.Polygon(points=np.array(points), point_um=0.25)
    shp.set_size(size_um=3.5)
    # center should not change
    assert np.allclose(shp.x, np.array(points)[:, 0].mean())
    assert np.allclose(shp.y, np.array(points)[:, 1].mean())
    assert shp.point_um == 0.25


def test_set_size_rectangle():
    shp = shapes.Rectangle(x=0, y=1, a=8, b=9, point_um=.25)
    shp.set_size(size_um=3.5)
    b_new = 3.5 / .25  # new size divided by point_um
    assert shp.x == 0
    assert shp.y == 1
    assert np.allclose(shp.a, b_new / 9 * 8)  # relative
    assert np.allclose(shp.b, b_new)
    assert shp.point_um == 0.25


def test_set_size_rectangle_2():
    shp = shapes.Rectangle(x=0, y=1, a=10, b=9, point_um=.25)
    shp.set_size(size_um=3.5)
    a_new = 3.5 / .25  # new size is divided by point_um
    assert shp.x == 0
    assert shp.y == 1
    assert shp.a == a_new
    assert shp.b == a_new / 10 * 9  # relative
    assert shp.point_um == 0.25


def test_shapes_copy():
    ell = shapes.Ellipse(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    ell2 = ell.copy()
    ell2.x = 10
    assert ell.x == 0
    cir = shapes.Circle(x=0, y=1, r=8, point_um=1)
    cir2 = cir.copy()
    cir2.r = 10
    assert cir.r == 8
    rec = shapes.Rectangle(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    rec2 = rec.copy()
    rec2.b = 20
    assert rec.b == 11
    pol = shapes.Polygon(points=np.array([[0, 1], [0, 0], [1, 0]]), point_um=1)
    pol2 = pol.copy()
    pol2.points[0, 0] = 100
    assert np.all(pol.points[0] == [0, 1])


def test_shapes_create():
    ell = shapes.Ellipse(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    assert ell.b == 11
    cir = shapes.Circle(x=0, y=1, r=8, point_um=1)
    assert cir.a == cir.b == 8
    rec = shapes.Rectangle(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    assert rec.b == 11
    pol = shapes.Polygon(points=[[0, 1], [0, 0], [1, 0]], point_um=1)
    assert pol.points[0, 1] == 1


def test_shapes_repr():
    ell = shapes.Ellipse(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    assert "Ellipse(x=0, y=1, a=10, b=11, phi=2, point_um=1)" in repr(ell)
    assert repr(ell).startswith("<")
    assert repr(ell).endswith(">")
    cir = shapes.Circle(x=0, y=1, r=8, point_um=1)
    assert "Circle(x=0, y=1, r=8, point_um=1)" in repr(cir)
    assert repr(cir).startswith("<")
    assert repr(cir).endswith(">")
    rec = shapes.Rectangle(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    assert "Rectangle(x=0, y=1, a=10, b=11, phi=2, point_um=1)" in repr(rec)
    assert repr(rec).startswith("<")
    assert repr(rec).endswith(">")
    pol = shapes.Polygon(points=[[0, 1], [0, 0], [1, 0]], point_um=1)
    assert "Polygon(\n[[0. 1.]\n [0. 0.]\n [1. 0.]], point_um=1)" in repr(pol)
    assert repr(pol).startswith("<")
    assert repr(pol).endswith(">")


def test_shapes_str():
    ell = shapes.Ellipse(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    assert f"{ell}" == "Ellipse x=0µm, y=1µm, a=10µm, b=11µm, phi=2rad"
    cir = shapes.Circle(x=0, y=1, r=8, point_um=1)
    assert f"{cir}" == "Circle x=0µm, y=1µm, r=8µm"
    rec = shapes.Rectangle(x=0, y=1, a=10, b=11, phi=2, point_um=1)
    assert f"{rec}" == "Rectangle x=0µm, y=1µm, a=10µm, b=11µm, phi=2rad"
    pol = shapes.Polygon(points=[[0, 1], [0, 0], [1, 0]], point_um=1)
    assert f"{pol}".replace(" ", "") == \
           "Polygon\n(0.0,1.0)µm\n(0.0,0.0)µm\n(1.0,0.0)µm"


def test_translate_circle():
    shp = shapes.Circle(x=0, y=1, r=8, point_um=.25)
    shp.translate(dx=1.4, dy=-1.6)
    assert np.allclose(shp.x, 1.4)
    assert np.allclose(shp.y, -.6)


def test_translate_ellipse():
    shp = shapes.Ellipse(x=0, y=1, a=8, b=7, point_um=.25)
    shp.translate(dx=1.4, dy=-1.6)
    assert np.allclose(shp.x, 1.4)
    assert np.allclose(shp.y, -.6)
    assert shp.a == 8
    assert shp.b == 7


def test_translate_polygon():
    points = [[4, 8], [12, 8], [12, 10], [4, 10]]
    shp = shapes.Polygon(points=np.array(points), point_um=0.25)
    shp.translate(dx=1.4, dy=-1.6)
    assert np.allclose(shp.x, np.array(points)[:, 0].mean() + 1.4)
    assert np.allclose(shp.y, np.array(points)[:, 1].mean() - 1.6)
    assert np.all(shp.points[0] == np.array([4+1.4, 8-1.6]))


def test_translate_rectangle():
    shp = shapes.Rectangle(x=0, y=1, a=8, b=7, point_um=.25)
    shp.translate(dx=1.4, dy=-1.6)
    assert np.allclose(shp.x, 1.4)
    assert np.allclose(shp.y, -.6)
    assert shp.a == 8
    assert shp.b == 7


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
