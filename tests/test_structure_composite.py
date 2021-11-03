import json
import pathlib

import numpy as np
import pytest

from impose import data
from impose.structure import StructureComposite, StructureLayer
from impose.geometry import shapes

data_path = pathlib.Path(__file__).parent / "data"


def test_append_duplicate_label():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sl2 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(x=1, y=0, a=12, b=10, phi=0), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)
    with pytest.raises(ValueError, match="already exists"):
        sc1.append(sl2)


def test_append_wrong_point_um():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Ellipse(x=1, y=0, a=12, b=10, phi=0), 1)],
        point_um=1.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)
    with pytest.raises(ValueError, match="point_um"):
        sc1.append(sl2)


def test_base():
    sc = StructureComposite()
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Ellipse(a=9), 1)],
        point_um=0.5,
    )
    sc.append(sl)
    sc.append(sl2)

    # __getitem__
    assert sc["test layer"] == sl
    assert sc["test layer 2"] == sl2
    assert sc[0] == sl
    assert sc[1] == sl2
    # __contains__
    assert "test layer" in sc
    assert sl2 in sc
    # __len__
    assert len(sc) == 2
    # point_um
    assert sc.point_um == sc.point_um


def test_change_layer_label():
    sc = StructureComposite()
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    sc.append(sl)
    sc.append(sl2)

    # rename to other name
    with pytest.raises(ValueError, match="already exists!"):
        sc.change_layer_label("test layer", "test layer 2")

    # rename basic
    sc.change_layer_label("test layer", "abc")
    assert sc[0].label == "abc"


def test_change_layer_label_same():
    sc = StructureComposite()
    sl = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(a=10), 1)],
        point_um=0.5,
    )
    sc.append(sl)

    # rename to same name
    sc.change_layer_label("test layer", "test layer")
    assert sc[0].label == "test layer"


def test_extract_data():
    ds = data.DataSource(data_path / "brillouin.h5")
    with (data_path / "brillouin.impose-composite").open() as fd:
        state = json.load(fd)
    sc = StructureComposite()
    sc.__setstate__(state)
    ed = sc.extract_data(data_source=ds, channels=["BrillouinShift"])
    assert ed["central canal"]["BrillouinShift"][0] == 43.79577394884312
    assert np.allclose(ed["central canal"]["BrillouinShift"].mean(),
                       43.77485558278776,
                       atol=0, rtol=1e-12)


def test_index():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sc = StructureComposite()
    sc.append(sl1)

    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Rectangle(x=0, y=1, a=10, b=5, phi=np.pi/2), 1)],
        point_um=0.5,
    )
    sc.append(sl2)

    assert sc.index("test layer") == 0
    assert sc.index(sl1) == 0
    assert sc.index("test layer 2") == 1
    assert sc.index(sl2) == 1
    with pytest.raises(KeyError, match="Could not find"):
        sc.index("test layer 47")
    sl3 = StructureLayer(
        label="test layer 47",
        geometry=[(shapes.Rectangle(x=0, y=1, a=10, b=5, phi=np.pi/2), 1)],
        point_um=0.5,
    )
    with pytest.raises(KeyError, match="Could not find"):
        sc.index(sl3)


def test_load_json():
    with (data_path / "brillouin.impose-composite").open() as fd:
        state = json.load(fd)
    sc = StructureComposite()
    sc.__setstate__(state)
    assert sc.layers[0].label == "notochord"
    assert sc.layers[1].label == "spinal cord"
    assert sc.layers[2].label == "central canal"
    assert sc["notochord"].point_um == 0.170773678164702
    ishape = sc["central canal"].geometry[0][0]
    assert isinstance(ishape, shapes.Circle)
    assert ishape.r == 1.814469830816729
    assert ishape.x == 36.84583909675443


def test_point_signature_circle():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Circle(x=1, y=0, r=7, phi=0), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)

    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Circle(x=0, y=1, r=7, phi=-np.pi/2), 1)],
        point_um=0.5,
    )
    sc2 = StructureComposite()
    sc2.append(sl2)

    assert sl1 != sl2
    assert sc1 != sc2
    assert sc1.geometry_identical_to(sc2)


def test_point_signature_ellipse():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Ellipse(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)

    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Ellipse(x=0, y=1, a=10, b=5, phi=np.pi/2), 1)],
        point_um=0.5,
    )
    sc2 = StructureComposite()
    sc2.append(sl2)

    assert sl1 != sl2
    assert sc1 != sc2
    assert sc1.geometry_identical_to(sc2)


def test_point_signature_polygon():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Polygon(points=[[0, 0], [0, 1], [2, 1]]), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)

    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Polygon(points=[[1, 1], [2, 1], [2, -1]]), 1)],
        point_um=0.5,
    )
    sc2 = StructureComposite()
    sc2.append(sl2)

    assert sl1 != sl2
    assert sc1 != sc2
    assert sc1.geometry_identical_to(sc2)


def test_point_signature_rectangle():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)

    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Rectangle(x=0, y=1, a=10, b=5, phi=np.pi/2), 1)],
        point_um=0.5,
    )
    sc2 = StructureComposite()
    sc2.append(sl2)

    assert sl1 != sl2
    assert sc1 != sc2
    assert sc1.geometry_identical_to(sc2)


def test_remove():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sc = StructureComposite()
    sc.append(sl1)

    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Rectangle(x=0, y=1, a=10, b=5, phi=np.pi/2), 1)],
        point_um=0.5,
    )
    sc.append(sl2)

    sc.remove("test layer")
    assert sl1 not in sc
    assert len(sc) == 1


def test_repr():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)
    assert repr(sc1).startswith("<StructureComposite: (1 layers)")


def test_str():
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=1, y=0, a=10, b=5, phi=0), 1)],
        point_um=0.5,
    )
    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Ellipse(x=1, y=0, a=12, b=10, phi=0), 1)],
        point_um=0.5,
    )
    sc1 = StructureComposite()
    sc1.append(sl1)
    sc1.append(sl2)
    assert "Ellipse" in str(sc1)
    assert "Rectangle" in str(sc1)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
