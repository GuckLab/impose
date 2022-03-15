from collections import OrderedDict

import imageio
import numpy as np


def load_img(path):
    """Load image files

    Pixel size is set to 1µm.

    Please see :func:`impose.formats.load` for more information.
    """
    img = imageio.imread(path)

    # Data
    channels = OrderedDict()

    if len(img.shape) == 2:
        channels["gray"] = img
    else:
        names = "RGBA"
        for ii in range(img.shape[2]):
            channels[names[ii]] = img[:, :, ii]

    # Metadata
    meta = {
        "pixel size x": 1,
        "pixel size y": 1,
        "pixel size z": np.nan,
        "shape": (img.shape[0], img.shape[1], 1),
    }

    return channels, meta
