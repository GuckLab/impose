import numpy as np

from impose import util


def test_basic_dicts():
    d1 = {"a": 2}
    d2 = {"a": 2}
    assert util.equal_states(d1, d2)
    d2["a"] = 3
    assert not util.equal_states(d1, d2)


def test_nan_dicts():
    d1 = {"a": 2, "b": np.nan}
    d2 = {"a": 2, "b": np.nan}
    assert util.equal_states(d1, d2)
    d2["b"] = 3.0
    assert not util.equal_states(d1, d2)


def test_nan_list():
    d1 = ["a", 2, "b", np.nan]
    d2 = ["a", 2, "b", np.nan]
    assert util.equal_states(d1, d2)
    d2[-1] = 2
    assert not util.equal_states(d1, d2)


def test_wrong_length():
    d1 = ["a", 2, "b", np.nan]
    d2 = ["a", 2, "b", np.nan]
    assert util.equal_states(d1, d2)
    d2.pop(-1)
    assert not util.equal_states(d1, d2)


def test_wrong_type():
    d1 = ["a", 2, "b", [np.nan]]
    d2 = ["a", 2, "b", np.nan]
    assert not util.equal_states(d1, d2)


def test_wrong_type2():
    d1 = ["a", 2, "b", np.nan]
    d2 = ["a", 2, "b", [np.nan]]
    assert not util.equal_states(d1, d2)
