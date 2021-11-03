import pathlib
import tempfile
import zipfile

import numpy as np

from impose import formats


data_path = pathlib.Path(__file__).parent / "data"


def get_czi():
    td = pathlib.Path(tempfile.mkdtemp(prefix="impose_czi_"))
    with zipfile.ZipFile(data_path / "lsm-fish.zip") as arc:
        arc.extractall(path=td)
    return td / "lsm-fish.czi"


def test_load_czi():
    path = get_czi()
    data, meta = formats.load(path)

    # check metadata
    assert meta["pixel size x"] == 1.65728515625
    assert meta["pixel size y"] == 1.65728515625
    assert np.isnan(meta["pixel size z"])
    assert meta["shape"] == (512, 512, 1)
    assert "mCher" in meta["channel hues"]
    assert "T-PMT" in meta["channel hues"]
    assert meta["signature"] == "68a9b6f5a47bf6ca36164312c5f88b41"

    assert data["mCher"].shape == (512, 512, 1)
    assert data["mCher"][10, 10, 0] == 1
    assert data["mCher"][205, 227, 0] == 255
    assert data["mCher"][113, 206, 0] == 123


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
