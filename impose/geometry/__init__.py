# flake8: noqa: F401
import pyqtgraph as pg

from . import mask
from . import shapes


def pg_roi_to_impose_shape(roi, tr, point_um):
    """Convenience method for converting a pyqtgraph ROI to an impose shape"""
    if isinstance(roi, pg.CircleROI):
        return shapes.Circle.from_pg_roi(roi, tr, point_um)
    elif isinstance(roi, pg.EllipseROI):
        return shapes.Ellipse.from_pg_roi(roi, tr, point_um)
    elif isinstance(roi, pg.PolyLineROI):
        return shapes.Polygon.from_pg_roi(roi, tr, point_um)
    elif isinstance(roi, pg.RectROI):
        return shapes.Rectangle.from_pg_roi(roi, tr, point_um)
    else:
        raise NotImplementedError("Shape '{}' not implemented!".format(roi))
