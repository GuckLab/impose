import pathlib
import shutil
import tempfile

import h5py
import numpy as np
import pytest

from impose import data


data_path = pathlib.Path(__file__).parent / "data"


def test_ds_bad_path():
    path = data_path / "does-not-exist.h5"
    with pytest.raises(FileNotFoundError):
        data.DataSource(path)


def test_ds_base():
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)

    assert "BrillouinShift" in ds.data_channels
    assert ds.shape == (1, 51, 71)
    assert ds.metadata["stack"]["pixel size y"] == 2
    assert ds.get_pixel_size() == (2.0, 2.0)
    assert ds.path == path
    assert ds.data_channels["BrillouinShift"][0, 10, 20] == 44.53328501973178


def test_ds_equal():
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)
    ds2 = data.DataSource(path)
    assert ds == ds2
    ds.metadata["blend"]["mode"] = "rgb"
    ds2.metadata["blend"]["mode"] = "hsv"
    assert ds != ds2


def test_ds_get_image_size_um():
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)
    imsize_um = ds.get_image_size_um()
    assert np.allclose(imsize_um, [102, 142])


def test_ds_get_pixel_size():
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)
    imsize_um = ds.get_pixel_size()
    assert np.allclose(imsize_um, [2, 2])


def test_ds_get_voxel_depth():
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)
    vd = ds.get_voxel_depth()
    assert np.isnan(vd), "because it is 2D"


def test_update_metadata():
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)
    assert ds.metadata["stack"]["pixel size y"] == 2
    assert ds.metadata["stack"]["pixel size z"] == 2
    ds.update_metadata({"stack": {"pixel size y": 3}})
    assert ds.metadata["stack"]["pixel size y"] == 3
    assert ds.metadata["stack"]["pixel size z"] == 2


def test_ds_with_nans():
    # create a copy that has nan-values
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="impose_tests_"))
    path = tmpdir / "brillouin_with_nan.h5"
    shutil.copy2(data_path / "brillouin.h5", path)
    with h5py.File(path, "a") as h5:
        h5["BrillouinShift"][0, :, :] = np.nan

    ds = data.DataSource(path)
    img = ds.get_image()
    # sanity check
    assert np.sum(np.isnan(img)) == 153
    assert np.allclose(img[0][1][0], 0.14016421516699523, atol=0)


def test_ds_signature_wrong():
    """Test whether bad signature raises warning"""
    path = data_path / "brillouin.h5"
    ds = data.DataSource(path)
    state = ds.__getstate__()
    state["metadata"]["signature"] = "peter"
    # now attempt to load it again
    with pytest.warns(
            data.DataSourceSignatureMismatchWarning,
            match="expected 627ccaa50d2b7447ebf64796e10f8794, got peter"):
        ds.__setstate__(state)
    assert ds.signature == "peter"


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
