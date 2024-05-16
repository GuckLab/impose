from collections import OrderedDict
from xml.dom.minidom import parseString

import numpy as np
import tifffile


def load_ometif(path):
    """Load .ome.tif files

    Please see :func:`impose.formats.load` for more information.
    """
    with tifffile.TiffFile(path) as tif:
        if not tif.is_ome:
            raise NotImplementedError(
                f"Could not load ome_metadata from file {path}. Please ask "
                f"for implementing support for your file format.")
        ome_meta = parseString(tif.ome_metadata)
        data = tif.asarray()

    channels = OrderedDict()
    name = ome_meta.getElementsByTagName("Image")[0].attributes["Name"].value
    channels[name] = data

    # Initial Metadata
    px = ome_meta.getElementsByTagName("Pixels")[0]
    xs = float(px.attributes["PhysicalSizeX"].value)
    ys = float(px.attributes["PhysicalSizeY"].value)

    # sanity checks
    assert px.attributes["PhysicalSizeXUnit"].value == "µm"
    assert px.attributes["PhysicalSizeYUnit"].value == "µm"

    # Channel names
    data_uuid = ome_meta.getElementsByTagName(
        "UUID")[0].childNodes[0].data.split(":")[-1]

    meta = {
        "pixel size x": xs,
        "pixel size y": ys,
        "pixel size z": np.nan,
        "shape": data.shape,
        "signature": data_uuid,
    }

    return channels, meta
