from collections import OrderedDict
from xml.etree import ElementTree

import numpy as np
import czifile
from skimage.color import rgb2hsv

from ..util import hashobj


def load_czi(path):
    """Load .czi files

    Please see :func:`impose.formats.load` for more information.
    """
    czi = czifile.CziFile(path)

    # Initial Metadata
    czi_meta = czi.metadata()
    root = ElementTree.fromstring(czi_meta)
    # sanity checks
    for item in root.findall(".//DefaultScalingUnit"):
        assert item.text == "µm"

    # Data
    data = czi.asarray()
    xid = czi.axes.index("X")
    yid = czi.axes.index("Y")
    zid = czi.axes.index("Z")
    cid = czi.axes.index("C")

    myslice = [0] * len(czi.shape)
    myslice[xid] = slice(None, None)
    myslice[yid] = slice(None, None)
    myslice[zid] = slice(None, None)

    # Channel names
    image = root.findall(".//Image")
    channel_names = []
    channel_hues = {}
    for im in image:
        dim = im.find("Dimensions")
        if dim:
            chn = dim.find("Channels")
            for ii, chi in enumerate(list(chn)):
                name = chi.get("Name", str(ii))
                channel_names.append(name)
                hue = color_hex2hue(chi.find("Color").text)
                channel_hues[name] = hue
            break
    else:
        # fallback
        channel_names = [str(ii) for ii in range(data.shape[cid])]

    channels = OrderedDict()
    for chid, chan in enumerate(channel_names):
        myslice[cid] = chid
        dslice = data[tuple(myslice)]
        # bring in x, y, z order
        a0, a1, a2 = np.argsort([xid, yid, zid])
        channels[str(chan)] = dslice.transpose(a0, a1, a2)

    # Other Metadata
    # lateral pixel size
    scaling = root.findall(".//ImageScaling")[0]
    if not scaling:
        raise ValueError("Could not determine lateral pixel size!")
    # pixel size
    pxsitem = scaling.findall("ImagePixelSize")[0]
    xs, ys = [float(it) for it in pxsitem.text.split(",")]
    # magnifications
    magns = []
    for cp in scaling.findall("ScalingComponent"):
        magns.append(float(cp.attrib["Magnification"]))
    mag = np.prod(magns)
    xs /= mag
    ys /= mag

    # voxel depth
    if data.shape[zid] > 1:
        for item in root.findall(".//AcquisitionBlock/SubDimensionSetups/"
                                 + "ZStackSetup/Interval/Distance/Value"):
            zs = float(item.text)
            # we are heuristic here, because the units cannot be trusted
            if zs < 1e-3:
                zs *= 1e6  # convert to um
            break
        else:
            raise ValueError("Could not determine spatial voxel depth!")
    else:
        zs = np.nan

    meta = {
        "pixel size x": xs,
        "pixel size y": ys,
        "pixel size z": zs,
        "shape": (data.shape[xid], data.shape[yid], data.shape[zid]),
        "signature": hashobj(czi_meta),
    }
    if channel_hues:
        meta["channel hues"] = channel_hues

    return channels, meta


def color_hex2hue(hex_string):
    """Convert a czi hex color string to hue

    Note that '#FF00FF5B' actually means '#00FF5B' here.
    The first two hex characters are something different.
    """
    color = hex_string.strip("#")
    r = int(color[2:4], 16)
    g = int(color[4:6], 16)
    b = int(color[6:8], 16)
    hue = rgb2hsv(np.array([r, g, b]))[0]
    return int(hue*255)
