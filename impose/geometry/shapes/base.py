import abc
import copy

import numpy as np


class BaseShape(abc.ABC):
    def __eq__(self, other):
        same_cls = self.__class__.__name__ == other.__class__.__name__
        try:
            same_sig = np.allclose(self.to_point_signature(),
                                   other.to_point_signature())
        except ValueError:
            # different number of points for polygon
            same_sig = False
        return same_cls and same_sig

    @abc.abstractmethod
    def __getstate__(self):
        """Get the state of the shape as a dictionary"""

    @abc.abstractmethod
    def __setstate__(self, state):
        """Set the state of the shape from a dictionary"""

    @abc.abstractmethod
    def __repr__(self):
        """String representation of the shape"""

    @abc.abstractmethod
    def __str__(self):
        """Human-readable string representing the shape"""

    def copy(self):
        return copy.deepcopy(self)

    @staticmethod
    @abc.abstractmethod
    def from_pg_roi(roi, tr, point_um):
        """Instantiate from a pyqtgraph ROI"""

    @abc.abstractmethod
    def set_size(self, size_um):
        """Convenience function that modifies the shape's size

        Size is defined individually and should refer to the
        largest extent of the shape.

        The position (self.x, self.y) should not change when
        the size is changed.

        If you would like to change the point size, use
        :func:`BaseShape.set_scale` instead. This function
        here exists only for visualization purposes (e.g.
        setting initial size of a shape).
        """

    @abc.abstractmethod
    def set_scale(self, point_um):
        """Set the point size in um"""

    @abc.abstractmethod
    def to_mask(self, shape, scale_x=1, scale_y=1):
        """Convert shape to mask

        Parameters
        ----------
        shape: tuple
            shape of the mask
        scale_x, scale_y: float
            scaling factors
        """

    @abc.abstractmethod
    def to_pg_roi(self, roi, tr):
        """Modify a pyqtgraph ROI to resemble this shape"""

    @abc.abstractmethod
    def to_point_signature(self):
        """Return shape as representative point cloud"""

    @abc.abstractmethod
    def translate(self, dx, dy):
        """Translate center coordinates

        Parameters
        ----------
        dx, dy: float
            Amount of points to translate the shape
        """

    @abc.abstractmethod
    def rotate(self, dphi):
        """Rotate shape

        Parameters
        ----------
        dphi: float
            Amount of radians to rotate
        """


def rotate_around_point(origin, points, angle):
    """Rotate points counterclockwise around an origin.

    Parameters
    ----------
    origin: list-like, length 2
        The x and y coordinates of the origin
    points: 2D ndarray of shape (N, 2)
        The N points as (x and y coordinates)
    angle: float
        Rotation angle in radians
    """
    ox, oy = origin
    px, py = points[:, 0], points[:, 1]

    qx = ox + np.cos(angle) * (px - ox) - np.sin(angle) * (py - oy)
    qy = oy + np.sin(angle) * (px - ox) + np.cos(angle) * (py - oy)
    points[:, 0] = qx
    points[:, 1] = qy
    return points
