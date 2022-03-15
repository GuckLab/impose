import numpy as np
from PyQt6 import QtCore
import pyqtgraph as pg

from ..geometry import pg_roi_to_impose_shape


class StructureCompositeROIs(QtCore.QObject):

    def __init__(self, image_view):
        """Visualization and modification of the ROIs of a StructureComposite

        Parameters
        ----------
        image_view: pyqtgraph.imageview.ImageView.ImageView
            This is where the image data is plotted to. The
            viewbox `image_view.view` is where the `pg.ROI`s are
            put.
        """
        super(StructureCompositeROIs, self).__init__()
        self.image_view = image_view
        #: The currently visualized StructureComposite
        self.structure_composite = None
        #: This is where :class:`pyqtrgaph.ROI`s go.
        self.rois = []
        #: Reference of all ROIs mapping to corresponding geometrical shapes
        self.roi2shape = {}

    @property
    def current_point_um(self):
        return self.structure_composite.point_um

    @property
    def viewbox(self):
        return self.image_view.view

    def clear(self, clear_structure_composite=True):
        if clear_structure_composite:
            self.structure_composite = None
        for roi in self.rois:
            roi.hide()
            self.viewbox.removeItem(roi)
        self.rois.clear()
        self.roi2shape.clear()

    def get_roi_transform(self, roi):
        """Return transform from ROI to data coordinates"""
        # get the image item
        img = self.image_view.getImageItem()
        # get the raw data
        data = np.array(self.image_view.image)[:, :, 0]
        # transform for mapping from geometry to data coordinates
        _, tr = roi.getArraySlice(data, img)
        return tr

    @QtCore.pyqtSlot(object)
    def on_layer_roi_changed(self, roi):
        """Update the StructureLayer if an ROI changed"""
        # We want to update `layer_shape` which is buried
        # somewhere in `self.structure_composite`.
        layer_shape = self.roi2shape[roi]
        tr = self.get_roi_transform(roi)
        temp_shape = pg_roi_to_impose_shape(roi, tr, self.current_point_um)
        layer_shape.__setstate__(temp_shape.__getstate__())

    def set_structure_composite(self, sc):
        self.structure_composite = sc
        self.update_pg_rois()

    def update_pg_rois(self):
        """Make sure the visualization matches `self.structure_composite`"""
        self.clear(clear_structure_composite=False)
        # definition of default ROI sizes and positions
        pos = 30
        size = 40
        roi_cls = {
            "Circle": (
                pg.CircleROI,
                dict(pos=[pos, pos], size=[size, size], pen=(1, 9))),
            "Ellipse": (
                pg.EllipseROI,
                dict(pos=[pos, pos], size=[size, size*2//3], pen=(2, 9))),
            "Polygon": (
                pg.PolyLineROI,
                dict(positions=[[pos, pos], [pos + 20, pos], [pos, pos + 30]],
                     pen=(4, 9), closed=True)),
            "Rectangle": (
                pg.RectROI,
                dict(pos=[pos, pos], size=[size, size*2//3], pen=(3, 9))),
        }
        for sl in self.structure_composite:
            for sh, _ in sl.geometry:
                # Create a blank pg.ROI
                name = sh.__class__.__name__
                rcl, kw = roi_cls[name]
                roi = rcl(**kw)
                if name == "Rectangle":
                    roi.addRotateHandle([1, 0], [0.5, 0.5])
                self.viewbox.addItem(roi)
                # Set the state of the ROI to match the given shape
                sh.to_pg_roi(roi=roi, tr=self.get_roi_transform(roi))
                # Keep a reference of this shape.
                self.roi2shape[roi] = sh
                # If the ROI changes, the shape inside the StructureLayer
                # inside the StructureComposite inside the
                # StructureCompositeStack also changes.
                roi.setPen(sl.color, width=1)
                roi.sigRegionChanged.connect(self.on_layer_roi_changed)
                self.rois.append(roi)

    def update_roi_colors(self):
        """Update the ROI colors (typically done after user interaction)"""
        for sl in self.structure_composite:
            for sh, _ in sl.geometry:
                for roi in self.roi2shape:
                    shr = self.roi2shape[roi]
                    if shr is sh:
                        roi.setPen(sl.color, width=1)
