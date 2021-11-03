import numbers

import numpy as np
import pyqtgraph as pg

from .. import mask

from .base import BaseShape, rotate_around_point


class Rectangle(BaseShape):
    def __init__(self, x=40, y=30, a=33, b=22, phi=0, point_um=1):
        """Rectangle

        Parameters
        ----------
        x, y: float
            center coordinates
        a, b: float
            side lengths
        phi: float
            rotation angle [rad]
        point_um: float
            point size in microns
        """
        self.x = float(x)
        self.y = float(y)
        self.a = float(a)
        self.b = float(b)
        self.phi = phi % (2 * np.pi)
        self.point_um = float(point_um)
        assert isinstance(point_um, numbers.Number)

    def __getstate__(self):
        return dict(x=self.x,
                    y=self.y,
                    a=self.a,
                    b=self.b,
                    phi=self.phi,
                    point_um=self.point_um)

    def __setstate__(self, state):
        self.x = state["x"]
        self.y = state["y"]
        self.a = state["a"]
        self.b = state["b"]
        self.phi = state["phi"]
        self.point_um = state["point_um"]

    def __repr__(self):
        fmtstr = "<Rectangle(x={:.5g}, y={:.5g}, a={:.3g}, b={:.3g}, " \
                 + "phi={:.3g}, point_um={:.3g}) at {}>"

        return fmtstr.format(self.x, self.y, self.a, self.b, self.phi,
                             self.point_um, hex(id(self)))

    def __str__(self):
        fmtstr = "Rectangle x={:.3g}µm, y={:.3g}µm, a={:.3g}µm, " \
                 + "b={:.3g}µm, phi={:.3g}rad"
        pum = self.point_um
        return fmtstr.format(self.x*pum, self.y*pum, self.a*pum, self.b*pum,
                             self.phi)

    @staticmethod
    def from_pg_roi(roi, tr, point_um):
        """Instantiate from a pyqtgraph ROI object"""
        bound = tr.mapRect(roi.boundingRect())
        center = bound.center()
        osize = pg.Point(roi.state["size"])
        sfact = np.sqrt(tr.m22()**2 + tr.m12()**2)
        rec = Rectangle(x=center.x()*sfact,
                        y=center.y(),
                        a=osize.x()*sfact,
                        b=osize.y()*sfact,
                        phi=np.deg2rad(roi.state["angle"] % 360),
                        point_um=point_um,
                        )
        return rec

    def set_scale(self, point_um):
        fact = point_um / self.point_um
        self.x /= fact
        self.y /= fact
        self.a /= fact
        self.b /= fact
        self.point_um = point_um

    def set_size(self, size_um):
        cursize = max(self.a, self.b) * self.point_um
        fact = size_um / cursize
        self.a *= fact
        self.b *= fact

    def to_mask(self, shape, scale_x=1, scale_y=1):
        return mask.rectangle(x=self.x,
                              y=self.y,
                              a=self.a,
                              b=self.b,
                              phi=self.phi,
                              shape=shape,
                              scale_x=scale_x,
                              scale_y=scale_y,
                              )

    def to_pg_roi(self, roi, tr):
        # One corner of pg.RectROI is the position
        dx = self.a / 2
        dy = self.b / 2
        xr = dx * np.cos(self.phi) - dy * np.sin(self.phi)
        yr = dx * np.sin(self.phi) + dy * np.cos(self.phi)

        sy = np.sqrt(tr.m22()**2 + tr.m12()**2)
        pos = [(self.x - xr)/sy,
               (self.y - yr)/sy
               ]
        state = roi.getState()
        roi.blockSignals(True)
        state["size"] = [self.a/sy, self.b/sy]
        state["angle"] = np.rad2deg(self.phi)
        state["pos"] = pos
        roi.setState(state)
        roi.blockSignals(False)

    def to_point_signature(self):
        """Return shape as representative point cloud [µm]"""
        points = np.array([[self.a/2, self.b/2],
                           [-self.a/2, self.b/2],
                           [self.a/2, -self.b/2]])
        points = rotate_around_point((0, 0), points, self.phi)
        points[:, 0] += self.x
        points[:, 1] += self.y
        return points * self.point_um

    def translate(self, dx, dy):
        """Translate center coordinates

        Parameters
        ----------
        dx, dy: float
            Amount of points to translate the shape
        """
        self.x += dx
        self.y += dy

    def rotate(self, dphi, origin=None):
        """Rotate shape

        Parameters
        ----------
        dphi: float
            Amount of radians to rotate
        origin: tuple of float
            Center coordinate around which to rotate
        """
        self.phi = (self.phi + dphi) % (2 * np.pi)
        if origin is not None:
            # rotate center with dphi
            center = np.array([[self.x, self.y]])
            center_r = rotate_around_point(origin, center, dphi)
            [[self.x, self.y]] = center_r
