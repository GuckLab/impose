import numbers
import pathlib

import numpy as np

from ..util import hashfile

# Naming conventions for formats:
# fmt_IMAGING-MODALITY_SPECIFIC_SOFTWARE.py
# IMAGING-MODALITY examples:
# - bf: Bright-Field Microscopy
# - bm: Brillouin Microscopy
# - fl: Fluorescence Microscopy

from .fmt_fl_zeiss import load_czi
from .fmt_bm_bmlab import load_h5
from .fmt_bf_generic import load_img


def load(path):
    """Load image data from microscopy files

    Parameters
    ----------
    path: str or pathlib.Path
        Path to the file

    Returns
    -------
    channels: collections.OrderedDict
        The keys are the names of the channels (`str`) and the values
        are numpy arrays (3d for volume data).
    meta: dict
        The corresponding metadata with the following keys:

        - "pixel size x": Pixel size along x [µm]
        - "pixel size y": Pixel size along y [µm]
        - "pixel size z": Pixel size along z [µm]
        - "shape": shape tuple for the underlying data (x, y[, z])
        - "signature": unique identifier for `path`
        - "channel hues": dict of channel colors; keys same as in
          `channels`, values integers from 0 to 255
    """
    path = pathlib.Path(path)
    channels, meta = suffix_dict[path.suffix](path)
    if "channel hues" not in meta:
        if len(channels) == 1:
            # yellow as default
            meta["channel hues"] = {list(channels.keys())[0]: 55}
        else:
            # equal distribution of hue values as default
            meta["channel hues"] = {}
            hues = np.linspace(0, 255, len(channels),
                               dtype=int, endpoint=False)
            for name, hue in zip(channels.keys(), hues):
                meta["channel hues"][name] = hue
    if "signature" not in meta:
        # Use the first 2^16 bytes as a file signature
        meta["signature"] = hashfile(path, blocksize=65536, count=1)
    for key in ["pixel size x", "pixel size y", "pixel size z"]:
        if key in meta:
            assert isinstance(meta[key], numbers.Number)

    return channels, meta


def get_signature(path):
    """Convenience function for getting the signature of a data file"""
    _, meta = load(path)
    return meta["signature"]


suffix_dict = {
    ".czi": load_czi,
    ".png": load_img,
    ".h5": load_h5,
    ".jpg": load_img,
}
