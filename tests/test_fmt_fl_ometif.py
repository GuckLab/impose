import pathlib
import tempfile
import zipfile

import numpy as np

from impose import formats


data_path = pathlib.Path(__file__).parent / "data"


def get_ometif():
    td = pathlib.Path(tempfile.mkdtemp(prefix="impose_ometif_"))
    with zipfile.ZipFile(data_path / "fmt_fl_ometif.zip") as arc:
        arc.extractall(path=td)
    return list(td.glob("*.ome.tif"))[0]


def test_load_ometif():
    path = get_ometif()
    data, meta = formats.load(path)

    # check metadata
    assert np.allclose(meta["pixel size x"], 0.2136)
    assert np.allclose(meta["pixel size y"], 0.2136)
    assert np.isnan(meta["pixel size z"])
    assert meta["shape"] == (512, 512)
    assert meta["signature"] == "a704111f-8e8d-40b0-9f55-4d649ef49167"
    chan = "Brillouin-2_MMStack_Default"
    assert data[chan].shape == (512, 512)
    assert data[chan][10, 10] == 246
    assert data[chan][205, 227] == 217
    assert data[chan][113, 206] == 280
