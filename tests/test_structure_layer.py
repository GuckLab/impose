import numpy as np

from impose.structure import StructureLayer
from impose.geometry import shapes


def test_copy():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    # create a copy
    sl2 = sl.copy()
    assert sl.geometry is not sl2.geometry

    # change geometry of the original structure layer
    sl.geometry[0][0].a = 11
    sl._label = "test layer 2"
    assert sl.geometry != sl2.geometry


def test_position_1():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(x=10, y=20), 1)],
        point_um=0.5,
    )
    assert np.all(sl.position_um == np.array([10, 20]) * .5)  # point_um


def test_position_2():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(x=10, y=20), 1),
                  (shapes.Ellipse(x=12, y=22), 1)
                  ],
        point_um=0.5,
    )
    assert np.all(sl.position_um == np.array([11, 21]) * .5)  # point_um


def test_repr():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    assert "test layer" in repr(sl)


def test_scale():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    sl.set_scale(0.1)
    assert sl.geometry[0][0].point_um == 0.1
    assert sl.point_um == 0.1


def test_set_state():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    state = sl.__getstate__()

    state["label"] = "hans"
    state["point_um"] = 1.2
    state["color"] = (123, 124, 125)
    state["geometry"][0][2] = 3
    sl.__setstate__(state)
    assert sl.label == "hans"
    assert sl.point_um == 1.2
    assert sl.color == (123, 124, 125)
    assert sl.geometry[0][1] == 3


def test_translate():
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(x=10, y=20), 1),
                  (shapes.Rectangle(x=12, y=22), 1)
                  ],
        point_um=0.5,
    )
    sl.translate(dr_um=(1.1, -4.2))
    assert np.all(sl.position_um == (6.6, 6.3))


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
