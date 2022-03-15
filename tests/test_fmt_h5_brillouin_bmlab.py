import numpy as np

from impose import formats

from helpers import retrieve_data


def test_load_bmlab_brillouin():
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022.zip")
    data, meta = formats.load(paths[0])

    # check metadata
    assert meta["pixel size x"] == 1
    assert meta["pixel size y"] == 1
    assert np.isnan(meta["pixel size z"])
    assert meta["shape"] == (3, 5, 1)
    assert "brillouin_peak_position" in meta["channel hues"]

    # check data
    assert "brillouin_peak_position" in data
    assert data["brillouin_peak_position"].shape == (3, 5, 1)
    assert data["brillouin_peak_position"][2, 3, 0] == 62.28071301762982
    assert meta["signature"] == "25d6ae8774fc29417facc6c9dfe061e6"


def test_load_bmlab_brillouin_signature():
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022.zip")
    _, meta1 = formats.load(paths[0])
    _, meta2 = formats.load(paths[1])
    assert meta1["signature"] == meta2["signature"]
