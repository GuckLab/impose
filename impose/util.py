import collections.abc
import hashlib
import numbers
import pathlib

import numpy as np


def dict_update_nested(orig_dict, new_dict):
    """Update nested dictionaries (does not override subdicts)"""
    for k, v in new_dict.items():
        if isinstance(v, collections.abc.Mapping):
            orig_dict[k] = dict_update_nested(orig_dict.get(k, {}), v)
        else:
            orig_dict[k] = v
    return orig_dict


def equal_states(obj1, obj2):
    """Whether two states are equal or not"""
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        # convert to list (items)
        obj1 = list(obj1.items())
        obj2 = list(obj2.items())
    if isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
        if len(obj1) != len(obj2):
            return False
        else:
            for ii in range(len(obj1)):
                equal = equal_states(obj1[ii], obj2[ii])
                if not equal:
                    return False
            else:
                # zero-length list/tuple
                return True
    elif (isinstance(obj1, numbers.Number) and np.isnan(obj1)
            and isinstance(obj2, numbers.Number) and np.isnan(obj2)):
        return True
    else:
        equal = obj1 == obj2
    return equal


def hashfile(fname, blocksize=65536, count=0, constructor=hashlib.md5):
    """Compute md5 hex-hash of a file

    Parameters
    ----------
    fname: str or pathlib.Path
        path to the file
    blocksize: int
        block size in bytes read from the file
        (set to `0` to hash the entire file)
    count: int
        number of blocks read from the file
    constructor: callable
        hash algorithm constructor
    """
    hasher = constructor()
    fname = pathlib.Path(fname)
    with fname.open('rb') as fd:
        buf = fd.read(blocksize)
        ii = 0
        while len(buf) > 0:
            hasher.update(buf)
            buf = fd.read(blocksize)
            ii += 1
            if count and ii == count:
                break
    return hasher.hexdigest()


def hashobj(obj):
    """Compute md5 hex-hash of a Python object"""
    return hashlib.md5(obj2bytes(obj)).hexdigest()


def obj2bytes(obj):
    """Bytes representation of an object for hashing"""
    if isinstance(obj, str):
        return obj.encode("utf-8")
    elif isinstance(obj, pathlib.Path):
        return obj2bytes(str(obj))
    elif isinstance(obj, (bool, int, float)):
        return str(obj).encode("utf-8")
    elif obj is None:
        return b"none"
    elif isinstance(obj, np.ndarray):
        return obj.tobytes()
    elif isinstance(obj, tuple):
        return obj2bytes(list(obj))
    elif isinstance(obj, list):
        return b"".join(obj2bytes(o) for o in obj)
    elif isinstance(obj, dict):
        return obj2bytes(sorted(obj.items()))
    else:
        raise ValueError("No rule to convert object '{}' to string.".
                         format(obj.__class__))
