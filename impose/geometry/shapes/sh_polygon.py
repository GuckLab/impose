import numbers

import numpy as np
from scipy.spatial.distance import cdist

from .. import mask

from .base import BaseShape, rotate_around_point


class Polygon(BaseShape):
    def __init__(self, points=None, point_um=1):
        """Polygon

        Parameters
        ----------
        points: list-like
            List or array of (x, y) coordinates
        point_um: float
            point size in microns
        """
        if points is None:
            points = [[20, 20], [40, 50], [80, 10]]
        self.points = np.array(points, dtype=float)
        self.point_um = point_um
        assert isinstance(point_um, numbers.Number)

    def __getstate__(self):
        return dict(points=self.points.tolist(),
                    point_um=self.point_um)

    def __setstate__(self, state):
        self.points = np.array(state["points"])
        self.point_um = state["point_um"]

    def __repr__(self):
        fmtstr = "<Polygon(\n{}, point_um={:.3g}) at {}>"
        return fmtstr.format(self.points, self.point_um, hex(id(self)))

    def __str__(self):
        pum = self.point_um
        rstr = "Polygon "
        for pp in self.points:
            rstr += "  \n({}, {})µm".format(pp[0]*pum, pp[1]*pum)
        return rstr

    @staticmethod
    def from_pg_roi(roi, tr, point_um):
        """Instantiate from a pyqtgraph ROI object"""
        sfact = np.sqrt(tr.m22()**2 + tr.m12()**2)
        state = roi.getState()
        points0 = state["points"]
        points = np.zeros_like(points0)
        for ii in range(len(points0)):
            pi = tr.map(points0[ii])
            points[ii] = pi.x()*sfact, pi.y()
        poly = Polygon(points=points,
                       point_um=point_um,
                       )
        return poly

    @property
    def x(self):
        return np.mean(self.points[:, 0])

    @property
    def y(self):
        return np.mean(self.points[:, 1])

    def set_scale(self, point_um):
        fact = point_um / self.point_um
        self.points /= fact
        self.point_um = point_um

    def set_size(self, size_um):
        # get current center
        x0 = self.x
        y0 = self.y
        # get current size
        hdist = cdist(self.points, self.points, metric='euclidean')
        cursize = np.max(hdist) * self.point_um
        fact = size_um / cursize
        # make sure the new center is identical to the old center
        points = np.array(self.points, copy=True)
        points[:, 0] -= x0
        points[:, 1] -= y0
        points *= fact
        points[:, 0] += x0
        points[:, 1] += y0
        self.points[:] = points

    def to_mask(self, shape, scale_x=1, scale_y=1):
        return mask.polygon(points=self.points,
                            shape=shape,
                            scale_x=scale_x,
                            scale_y=scale_y,
                            )

    def to_pg_roi(self, roi, tr):
        # A pg polygon is already defined in the data coordinates
        sy = np.sqrt(tr.m22() ** 2 + tr.m12() ** 2)
        points = self.points.copy() / sy
        state = roi.getState()
        roi.blockSignals(True)
        state["angle"] = 0
        state["pos"] = (0, 0)
        state["points"] = [p for p in points]
        roi.setState(state)
        roi.blockSignals(False)

    def to_point_signature(self):
        """Return shape as representative point cloud"""
        return self.points * self.point_um

    def translate(self, dx, dy):
        """Translate center coordinates

        Parameters
        ----------
        dx, dy: float
            Amount of points to translate the shape
        """
        self.points[:, 0] += dx
        self.points[:, 1] += dy

    def rotate(self, dphi, origin=None):
        """Rotate shape

        Parameters
        ----------
        dphi: float
            Amount of radians to rotate
        origin: tuple of float
            Center coordinate around which to rotate
        """
        if origin is None:
            origin = (self.x, self.y)
        self.points[:] = rotate_around_point(origin=origin,
                                             points=self.points,
                                             angle=dphi)
