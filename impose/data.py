import warnings
from collections import OrderedDict
import copy
import pathlib

import numpy as np

from .flblend import FlBlend
from .formats import load
from .util import equal_states, dict_update_nested


class DataSourceSignatureMismatchWarning(UserWarning):
    pass


class DataChannel(dict):
    """One component of a DataSource"""

    def __init__(self, name, hue=128, brightness=128, contrast=128,
                 slice_width=1, reduce_method=None):
        super(DataChannel, self).__init__()
        self["name"] = name
        self["brightness"] = brightness
        self["contrast"] = contrast
        self["slice_width"] = slice_width
        self["reduce_method"] = reduce_method
        self["hue"] = hue


class DataSource:
    """Reproducible visualization of a slice through a 3D dataset"""

    def __init__(self, path):
        #: dataset path
        self.path = None
        #: data dictionary {"channel name": np.ndarray)
        self.data_channels = {}
        #: metadata dictionary
        self.metadata = {}
        #: current visualization snapshot
        self._snapshot = None
        self._initialize_from_path(path)

    def __eq__(self, other):
        return equal_states(self.__getstate__(), other.__getstate__())

    def __getitem__(self, item):
        return self.get_channel_data(item)

    def __getstate__(self):
        metadata = copy.deepcopy(self.metadata)
        # preserve order of OrderedDict for channels
        metadata["channels"] = list(metadata["channels"].items())
        state = {
            "path": str(self.path),
            "metadata": metadata,
        }
        return state

    def __setstate__(self, state):
        # `__setstate__` does not override `self.path` from `state`
        self._initialize_from_path(state["path"])
        metadata = state["metadata"]
        # make sure that stack-shape is a tuple
        stack_shape = metadata.get("stack", {}).get("shape")
        if isinstance(stack_shape, list):
            metadata["stack"]["shape"] = tuple(stack_shape)
        # repopulate OrderedDict for channels
        metadata["channels"] = OrderedDict(metadata["channels"])
        # verify data source signature (if present)
        orig_sig = self.metadata["signature"]
        state_sig = metadata.get("signature")
        if state_sig is not None and state_sig != orig_sig:
            warnings.warn(
                f"Signature verification failed for '{self.path}' (expected "
                f"{orig_sig}, got {state_sig})!'",
                DataSourceSignatureMismatchWarning)
        # update metadata dictionary
        dict_update_nested(self.metadata, metadata)
        # reset snapshot
        self._snapshot = None

    def _initialize_from_path(self, path):
        self.path = pathlib.Path(path).resolve()
        if not self.path.exists():
            raise FileNotFoundError(f"File does not exist: '{self.path}'")
        # extract the data and metadata
        data_channels, meta_orig = load(path)
        self.data_channels = data_channels
        meta_channels = OrderedDict()
        for name in data_channels:
            meta_channels[name] = DataChannel(
                name=name,
                hue=meta_orig["channel hues"][name],
            )
        # set initial channels
        # If the numbers is <= 3, select all by default, otherwise
        # select the first one.
        if len(data_channels) <= 3:
            channels_sel = list(data_channels.keys())
        else:
            channels_sel = [list(data_channels.keys())[0]]

        # Determine correct view plane, cut axis and view slice for data
        if 1 in meta_orig["shape"]:
            # we most-likely have a 2D image (or no usable data)
            cut_axis = meta_orig["shape"].index(1)
            view_plane = [0, 1, 2]
            view_plane.pop(cut_axis)
        else:
            # convenience default values for 3D stacks
            cut_axis = 0
            view_plane = [1, 2]
        view_slice = meta_orig["shape"][cut_axis] // 2

        meta_stack = {"shape": meta_orig["shape"]}
        for key in ["pixel size x", "pixel size y", "pixel size z"]:
            if key in meta_orig:
                meta_stack[key] = meta_orig[key]

        self.metadata = {
            "blend": {
                "mode": "hsv",
                "channels": channels_sel,
            },
            "channels": meta_channels,
            "slice": {
                "view plane": view_plane,
                "cut axis": cut_axis,
                "view slice": view_slice},  # refers to position in "cut axis"
            "signature": meta_orig["signature"],
            "stack": meta_stack,
        }
        self._snapshot = None

    @property
    def signature(self):
        return self.metadata["signature"]

    @property
    def shape(self):
        return self.metadata["stack"]["shape"]

    @property
    def snapshot(self):
        if self._snapshot is None:
            self.get_image()
        return self._snapshot

    def get_channel_data(self, name):
        cdat = self.data_channels[name]
        if len(cdat.shape) == 2:
            return cdat
        else:
            # Assemble tuple for slicing
            metasl = self.metadata["slice"]
            cslice = [0] * len(cdat.shape)
            for imax in metasl["view plane"]:
                cslice[imax] = slice(None, None)
            cslice[metasl["cut axis"]] = metasl["view slice"]
            return cdat[tuple(cslice)]

    def get_image(self):
        fb = FlBlend()
        for name in self.data_channels:
            if name in self.metadata["blend"]["channels"]:
                chimg = self.get_channel_data(name)
                cmet = self.metadata["channels"][name]
                fb.add_image(image=chimg,
                             hue=cmet["hue"],
                             brightness=cmet["brightness"],
                             contrast=cmet["contrast"])
        self._snapshot = fb.blend(self.metadata["blend"]["mode"])
        return self._snapshot

    def get_image_shape(self):
        """Return the 2D shape of the image returned by `get_image`"""
        name = list(self.data_channels.keys())[0]
        return self.get_channel_data(name).shape

    def get_image_size_um(self):
        """Return the size of the currently set image"""
        shape = self.get_image_shape()
        pxsize = self.get_pixel_size()
        return np.array(shape) * np.array(pxsize)

    def get_pixel_size(self):
        """Return pixel size for the current view in microns"""
        if len(self.shape) == 2:
            return (self.metadata["stack"]["pixel size x"],
                    self.metadata["stack"]["pixel size y"])
        else:
            ax1, ax2 = self.metadata["slice"]["view plane"]
            sizes = [self.metadata["stack"]["pixel size x"],
                     self.metadata["stack"]["pixel size y"],
                     self.metadata["stack"]["pixel size z"]]
            return sizes[ax1], sizes[ax2]

    def get_voxel_depth(self):
        """Return voxel depth for current view in microns"""
        if len(self.shape) == 2:
            return np.nan
        else:
            ax = self.metadata["slice"]["cut axis"]
            sizes = [self.metadata["stack"]["pixel size x"],
                     self.metadata["stack"]["pixel size y"],
                     self.metadata["stack"]["pixel size z"]]
            return sizes[ax]

    def update_metadata(self, meta_dict):
        """Update the metadata dictionary"""
        for sec in meta_dict:
            self.metadata[sec].update(meta_dict[sec])
