import pathlib
import shutil
import tempfile

import h5py
import numpy as np
import pytest

from impose import formats


data_path = pathlib.Path(__file__).parent / "data"


def test_load_brillouin():
    path = data_path / "brillouin.h5"
    data, meta = formats.load(path)

    # check metadata
    assert np.isnan(meta["pixel size x"])
    assert meta["pixel size y"] == 2
    assert meta["pixel size z"] == 2
    assert meta["shape"] == (1, 51, 71)
    assert "BrillouinShift" in meta["channel hues"]

    # check data
    assert "BrillouinShift" in data
    assert data["BrillouinShift"].shape == (1, 51, 71)
    assert data["BrillouinShift"][0, 10, 20] == 44.53328501973178
    assert meta["signature"] == "627ccaa50d2b7447ebf64796e10f8794"


def test_load_brillouin_invalid():
    path = data_path / "brillouin-invalid.h5"
    with pytest.raises(ValueError):
        formats.load(path)


def test_load_brillouin_with_nans():
    # create a copy that has nan-values
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="impose_tests_"))
    path = tmpdir / "brillouin_with_nan.h5"
    shutil.copy2(data_path / "brillouin.h5", path)
    with h5py.File(path, "a") as h5:
        h5["BrillouinShift"][0, :, :] = np.nan

    data, _ = formats.load(path)
    # sanity check (axes are swapped)
    assert np.all(np.isnan(data["BrillouinShift"][:, :, 0]))


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
