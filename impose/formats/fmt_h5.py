from collections import OrderedDict

import h5py
import numpy as np


def load_h5(path):
    """Load .h5 files from BMicro

    Please see :func:`impose.formats.load` for more information.
    """
    with h5py.File(path, "r") as h5:
        # Data
        chkeys = sorted(h5.keys())
        # find axis order
        k0 = chkeys[0]
        # sometimes this is str and sometimes bytes
        axes = np.string_(h5[k0].attrs["axisOrder"]).decode("utf-8")
        xid = axes.index("X")
        yid = axes.index("Y")
        zid = axes.index("Z")

        channels = OrderedDict()
        for chan in chkeys:
            dslice = h5[chan][:]
            if len(dslice.shape) != 3:
                raise ValueError(
                    "Invalid number of dimensions in '{}'. ".format(path)
                    + "Please verify the original Brillouin dataset.")
            channels[chan] = dslice.transpose(xid, yid, zid)

        # Metadata
        meta = {
            "pixel size x": np.array(h5.attrs["scaleX"]).item(),
            "pixel size y": np.array(h5.attrs["scaleY"]).item(),
            "pixel size z": np.array(h5.attrs["scaleZ"]).item(),
            "shape": channels[chkeys[0]].shape,
        }

    return channels, meta
