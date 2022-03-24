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


def test_load_bmlab_brillouin_2rep():
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022_2-rep.zip")
    data, meta = formats.load(paths[0])

    # check metadata
    assert meta["pixel size x"] == 1
    assert meta["pixel size y"] == 1
    assert np.isnan(meta["pixel size z"])
    assert meta["shape"] == (3, 5, 1)
    assert "rep-0_brillouin_peak_position" in meta["channel hues"]
    assert "rep-1_brillouin_peak_position" in meta["channel hues"]

    # check data
    assert "rep-0_brillouin_peak_position" in data
    assert data["rep-0_brillouin_peak_position"].shape == (3, 5, 1)
    assert data["rep-0_brillouin_peak_position"][2, 3, 0] == 55.53730853499501
    assert "rep-1_brillouin_peak_position" in data
    assert data["rep-1_brillouin_peak_position"].shape == (3, 5, 1)
    assert data["rep-1_brillouin_peak_position"][2, 3, 0] == 101.47705516241298

    assert meta["signature"] == "0f9dfe4cfe549859ac09ec0ead5bf58f"


def test_load_bmlab_brillouin_signature():
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022.zip")
    _, meta1 = formats.load(paths[0])
    _, meta2 = formats.load(paths[1])
    assert meta1["signature"] == meta2["signature"]
