import copy
import numbers

import numpy as np

from ..geometry import shapes as gshapes


class StructureLayer:
    def __init__(self, label, point_um, geometry, color=(255, 255, 255)):
        """Structure layer

        Parameters
        ----------
        label: str
            User-defined label of the layer
        point_um: float
            Point size in microns
        geometry: list of tuple of (impose.geometry.shapes.BaseShape, int)
            Each list entry is a tuple with (shape, masking_factor) where
            "masking_factor" means how the shape should be treated when a
            binary mask is created - it can be positive or negative and
            in the end the mask is thresholded with ">0". E.g. you can
            have one shape with a masking_factor of +1 and another smaller
            shape withing that first shape with a masking factor of -1 -
            which means that the smaller region will be excluded from
            the mask.
        """
        self._label = label
        #: The shapes and their intent
        self.geometry = geometry
        assert isinstance(geometry, list)
        assert len(geometry) > 0
        assert isinstance(geometry[0], tuple)
        assert isinstance(geometry[0][1], numbers.Integral)
        #: Point size in microns
        self.point_um = point_um
        #: Layer color
        self.color = color

    def __getstate__(self):
        gstate = []
        for ishape, fact in self.geometry:
            gstate.append([ishape.__class__.__name__,
                           ishape.__getstate__(),
                           fact])

        return dict(label=self.label,
                    point_um=self.point_um,
                    geometry=gstate,
                    color=tuple(self.color),
                    )

    def __setstate__(self, state):
        self._label = state["label"]
        self.point_um = state["point_um"]
        self.color = state["color"]
        # We have two options for geometry. Either we set each geometries
        # state or we reset the geometry. Because it is unclear what the
        # future use-cases of __setstate__ will be, we go with the reset
        # option for now.
        self.geometry.clear()
        self.geometry += StructureLayer._geometry_from_dict(state["geometry"])

    def __str__(self):
        return "StructureLayer: {} with {}".format(self.label, self.geometry)

    def __repr__(self):
        return "<StructureLayer: {} at {}>".format(self.label, hex(id(self)))

    @staticmethod
    def _geometry_from_dict(gdict):
        """Return the geometry object list from __getstate__ data"""
        clsd = {"Circle": gshapes.Circle,
                "Ellipse": gshapes.Ellipse,
                "Polygon": gshapes.Polygon,
                "Rectangle": gshapes.Rectangle,
                }
        geometry = []
        for name, state, fact in gdict:
            gobj = clsd[name](**state)
            geometry.append((gobj, fact))
        return geometry

    @staticmethod
    def from_state(state):
        """Instantiate a StructureLayer with a state (from __getstate__)"""
        geometry = StructureLayer._geometry_from_dict(state["geometry"])
        return StructureLayer(label=state["label"],
                              point_um=state["point_um"],
                              geometry=geometry,
                              color=copy.copy(state["color"]))

    @property
    def label(self):
        """User-defined label of the layer

        The label should only be changed via
        :func:`StructureComposite.change_layer_label` function to avoid
        name clashes.
        """
        return self._label

    @property
    def position_um(self):
        """Return the representative position of the layer [µm]"""
        x = np.mean([g[0].x for g in self.geometry])
        y = np.mean([g[0].y for g in self.geometry])
        return np.array([x, y]) * self.point_um

    def copy(self):
        geometry = copy.deepcopy(self.geometry)
        assert isinstance(geometry, list)
        sl = StructureLayer(
            label=self.label,
            geometry=geometry,
            point_um=self.point_um,
            color=copy.deepcopy(self.color),
        )
        return sl

    def extract_data(self, data_source, channels=None):
        """Extract the relevant data points from a data source

        Parameters
        ----------
        data_source: impose.data.DataSource
            Data source from which to extract data
        channels: list of str
            List of channel names for which to extract data

        Returns
        -------
        data: dict {str: np.ndarray}
            Dictionary with channels as keys and 1D np.ndarrays
            as values (extracted data points)
        """
        if channels is None:
            channels = sorted(data_source.data_channels.keys())
        mask = self.to_mask(data_source)
        data = {}
        for chn in channels:
            data[chn] = data_source[chn][mask]
        return data

    def rotate(self, dphi, origin_um=None):
        """Rotate the layer

        Parameters
        ----------
        dphi: float
            rotation angle [rad]
        origin_um: tuple of floats
            x-y-coordinates of the center of rotation [µm]
        """
        if origin_um is None:
            origin_um = self.position_um
        origin = np.array(origin_um) / self.point_um
        for sh, _ in self.geometry:
            sh.rotate(dphi=dphi, origin=origin)

    def set_scale(self, point_um):
        """Scale to new point size in microns"""
        self.point_um = point_um
        for (sh, _) in self.geometry:
            sh.set_scale(point_um)

    def to_mask(self, data_source):
        """Create a binary mask from this structure layer"""
        sx, sy = data_source.get_pixel_size()
        dshape = data_source.get_image_shape()
        accmask = np.zeros(dshape, dtype=int)
        for ii, (gshape, masking_factor) in enumerate(self.geometry):
            # The shape is defined with a pixel height (y) of 1.
            # Since pixel width and height are not equal, we have to
            # scale the x-value.
            maski = gshape.to_mask(shape=dshape,
                                   scale_x=sy/sx,
                                   scale_y=1,
                                   )
            accmask += maski * masking_factor
        return accmask > 0

    def to_point_signature(self):
        """Return geometry as representative points

        Returns
        -------
        sig: np.ndarray of shape (N, 3)
            Point signature. The first axis contains the signature
            points of all shapes. The second axis contains
            (x, y, fact, shape_index).
        """
        signature = []
        for ii, (sh, fac) in enumerate(self.geometry):
            for pp in sh.to_point_signature():
                signature.append([pp[0], pp[1], fac, ii])
        signature = np.array(signature)
        return signature

    def translate(self, dr_um):
        """Translate the layer by dr_um = (dx, dy) [µm]"""
        dr = np.array(dr_um) / self.point_um
        for sh, _ in self.geometry:
            sh.translate(dr[0], dr[1])
