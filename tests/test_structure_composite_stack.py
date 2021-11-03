import pathlib

import numpy as np

from impose.structure import (
    StructureComposite, StructureCompositeStack, StructureLayer)
from impose.geometry import shapes

data_path = pathlib.Path(__file__).parent / "data"


def make_sc(seed=42):
    np.random.seed(seed)
    sl1 = StructureLayer(
        label="test layer",
        geometry=[(shapes.Rectangle(x=np.random.rand(),
                                    y=np.random.rand(),
                                    a=np.random.rand(),
                                    b=np.random.rand(),
                                    phi=0), 1)],
        point_um=0.5,
    )
    sl2 = StructureLayer(
        label="test layer 2",
        geometry=[(shapes.Rectangle(x=np.random.rand(),
                                    y=np.random.rand(),
                                    a=np.random.rand(),
                                    b=np.random.rand(),
                                    phi=0), 1)],
        point_um=0.5,
    )
    sc = StructureComposite()
    sc.append(sl1)
    sc.append(sl2)
    return sc


def test_add():
    sc1 = make_sc(1)
    sc2 = make_sc(2)
    sc3 = make_sc(2)
    sc4 = make_sc(2)

    scs1 = StructureCompositeStack()
    scs1.append(sc1)
    scs1.append(sc2)

    scs2 = StructureCompositeStack()
    scs2.append(sc3)
    scs2.append(sc4)

    # sanity check
    assert scs1 != scs2

    scs3 = scs2 + scs1
    assert scs3[0] == scs2[0]
    assert scs3[1] == scs2[1]
    assert scs3[2] == scs1[0]
    assert scs3[3] == scs1[1]


def test_add_left():
    sc1 = make_sc(1)
    sc2 = make_sc(2)
    sc3 = make_sc(2)
    sc4 = make_sc(2)

    scs1 = StructureCompositeStack()
    scs1.append(sc1)
    scs1.append(sc2)

    scs2 = StructureCompositeStack()
    scs2.append(sc3)
    scs2.append(sc4)

    scs2 += scs1
    assert scs2[2] == scs1[0]
    assert scs2[3] == scs1[1]


def test_basic():
    sc1 = make_sc(1)
    sc2 = make_sc(2)
    assert sc1 != sc2, "sanity check"
    scs = StructureCompositeStack()
    scs.append(sc1)
    scs.append(sc2)
    assert len(scs) == 2


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
