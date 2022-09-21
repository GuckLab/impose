import numpy as np

from impose import formats

from helpers import retrieve_data


def test_load_bmlab_brillouin():
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022_water.zip")
    data, meta = formats.load(paths[0])

    # check metadata
    assert meta["pixel size x"] == 1
    assert meta["pixel size y"] == 1
    assert np.isnan(meta["pixel size z"])
    assert meta["shape"] == (3, 5, 1)
    assert "brillouin_peak_position_f" in meta["channel hues"]

    # check data
    assert "brillouin_peak_position_f" in data
    assert data["brillouin_peak_position_f"].shape == (3, 5, 1)
    assert data["brillouin_peak_position_f"][2, 3, 0] == 7.418597699375756
    assert meta["signature"] == "7692028641e09f26ad0c8caf010ecaeb"


def test_load_bmlab_brillouin_2rep():
    paths =\
        retrieve_data("fmt_brillouin-h5_bmlab-session_2022_water_2-rep.zip")
    data, meta = formats.load(paths[0])

    # check metadata
    assert meta["pixel size x"] == 1
    assert meta["pixel size y"] == 1
    assert np.isnan(meta["pixel size z"])
    assert meta["shape"] == (3, 5, 1)
    assert "rep-0_brillouin_peak_position_f" in meta["channel hues"]
    assert "rep-1_brillouin_peak_position_f" in meta["channel hues"]

    # check data
    assert "rep-0_brillouin_peak_position_f" in data
    assert data["rep-0_brillouin_peak_position_f"].shape == (3, 5, 1)
    assert data["rep-0_brillouin_peak_position_f"][2, 3, 0] ==\
           7.414767296701641
    assert "rep-1_brillouin_peak_position_f" in data
    assert data["rep-1_brillouin_peak_position_f"].shape == (3, 5, 1)
    assert data["rep-1_brillouin_peak_position_f"][2, 3, 0] ==\
           7.4293433545770124

    assert meta["signature"] == "0fa3675745a06d6c54184aa95873280e"


def test_load_bmlab_brillouin_signature():
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022_water.zip")
    _, meta1 = formats.load(paths[0])
    _, meta2 = formats.load(paths[1])
    assert meta1["signature"] == meta2["signature"]
