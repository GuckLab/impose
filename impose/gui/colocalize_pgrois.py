import numpy as np
from PyQt6 import QtCore
import pyqtgraph as pg
from pyqtgraph import functions as fn

from ..geometry import pg_roi_to_impose_shape
from ..geometry.shapes import rotate_around_point
from ..structure import StructureComposite


class StructureCompositeGroupedROIs(QtCore.QObject):
    structure_changed = QtCore.pyqtSignal()

    def __init__(self, image_view):
        """A list of ROIs that can be moved and rotated together"""
        # We have to subclass from QObject, otherwise signals and
        # slots won't work.
        super(StructureCompositeGroupedROIs, self).__init__()
        self.image_view = image_view
        self.rois = []
        self.active_roi = None
        self._initial_states = []  # initial ROI states
        self._rotation_center = None  # rotation center set at rotation init
        self._scene_transforms = []  # transforms for all ROIs during rotation
        #: currently active StructureLayer (used in colocalize)
        self.active_structure_layer = None
        self._point_um = None  # for debugging
        self._structur_layer_rois = []  # keeps track of ROIs for each SL

    def __getitem__(self, index):
        return self.rois[index]

    def __iter__(self):
        return iter(self.rois)

    @property
    def viewbox(self):
        return self.image_view.view

    def append(self, roi):
        """Modify an ROI according to colocalize policy and append it"""
        roi.blockSignals(True)
        # disable resizing feature of pg.ROI
        roi.resizable = False
        # disable rotation feature by setting rotateModifier to None
        # (we still need `roi.rotatable == True`)
        roi.mouseDragHandler.rotateModifier = None
        roi.sigRegionChangeStarted.connect(self.on_change_started)
        roi.sigRegionChangeFinished.connect(self.on_change_finished)
        roi.sigRegionChanged.connect(self.on_change_finished)
        roi.setAcceptedMouseButtons(
            QtCore.Qt.MouseButton.LeftButton)  # allow clicking
        roi.sigClicked.connect(self.update_structure_geometry)
        self.rois.append(roi)
        self._initial_states.append(roi.saveState())

        # Add rotation handles where appropriate
        if isinstance(roi, pg.RectROI):
            roi.addRotateHandle([1, 0], [0.5, 0.5])
        elif isinstance(roi, pg.CircleROI):
            # Add rotate handle for circles, because rotating a
            # circle rotates everything around it in colocalize.
            roi.addRotateHandle([0.5, 0], [0.5, 0.5])

        for hh in roi.handles:
            if hh["type"] == "s":
                # Remove scale handles
                roi.removeHandle(hh["item"])
            elif hh["type"] == "f":
                # Hide polygon drag handles
                hh["item"].hide()
        roi.blockSignals(False)

    def clear(self):
        for roi in self.rois:
            self.viewbox.removeItem(roi)
        self.rois.clear()
        self.active_roi = None
        self._scene_transforms.clear()
        self._initial_states.clear()
        self._rotation_center = None
        self.active_structure_layer = None
        self._structur_layer_rois.clear()

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
    def on_change_finished(self, roi):
        try:
            old_state = self._initial_states[self.rois.index(roi)]
        except ValueError:
            old_state = {"angle": None, "pos": None}
        new_state = roi.saveState()
        # compute the transform from old_state to new_state
        if old_state["angle"] != new_state["angle"]:
            rotate_center = self._rotation_center
            rotate_angle = new_state["angle"] - old_state["angle"]
            translate = None
        else:
            rotate_angle = None
            rotate_center = None
            if old_state["pos"] != new_state["pos"]:
                translate = np.array(
                    new_state["pos"]) - np.array(old_state["pos"])
            else:
                translate = None
        for ii, rr in enumerate(self.rois):
            if rr is not roi:
                rr.blockSignals(True)
                rr.setState(self._initial_states[ii])
                # transform the geometry
                if rotate_angle is not None:
                    tr = fn.invertQTransform(self._scene_transforms[ii])
                    center = tr.map(rotate_center)
                    rr.setAngle(angle=rr.state["angle"] + rotate_angle,
                                centerLocal=center)
                elif translate is not None:
                    rr.translate(translate, snap=False)
                rr.blockSignals(False)
        self.update_structure_geometry()

    @QtCore.pyqtSlot(object)
    def on_change_started(self, roi):
        self._initial_states.clear()
        self._initial_states += [r.saveState() for r in self.rois]
        # determine scene rotation center
        tr = roi.sceneTransform()
        b = tr.mapRect(roi.boundingRect())
        self._rotation_center = b.center()
        self._scene_transforms.clear()
        self._scene_transforms += [r.sceneTransform() for r in self.rois]
        self.active_roi = roi
        for sl, _, rr in self._structur_layer_rois:
            if roi is rr:
                self.active_structure_layer = sl
                break
        else:
            raise ValueError("Could not find active structure!")

    def set_structure_composite(self, cs, vis):
        """Visualize a specific structure composite"""
        assert isinstance(cs, StructureComposite)
        # remove all ROIs and structure information
        self.clear()
        if not cs:
            # Nothing to display, abort here.
            return
        self.active_structure_layer = cs[0]
        # add new ROIs
        roi_cls = {
            "Circle": pg.CircleROI,
            "Ellipse": pg.EllipseROI,
            "Polygon": ColocPolyLineROI,
            "Rectangle": pg.RectROI,
        }
        for sl in cs:
            for ii, (ishape, _) in enumerate(sl.geometry):
                key = ishape.__class__.__name__
                roi = roi_cls[key](pos=(0, 0), size=(10, 10))
                self.viewbox.addItem(roi)

                tr = vis.get_roi_transform(roi)
                roi.blockSignals(True)
                ishape.to_pg_roi(roi, tr)
                # cosmetics
                roi.setPen(sl.color, width=1)
                roi.blockSignals(False)
                self.append(roi)
                self._structur_layer_rois.append([sl, ii, roi])

    def update_roi_geometry(self):
        """Update all pyqtgraph ROIs with their corresponding geometry data"""
        for sl, gid, roi in self._structur_layer_rois:
            tr = self.get_roi_transform(roi)
            sl.geometry[gid][0].to_pg_roi(roi, tr)
        self.structure_changed.emit()

    @QtCore.pyqtSlot()
    def update_structure_geometry(self):
        """Update the strucure layer of the all pyqtgraph ROIs"""
        for sl, gid, roi in self._structur_layer_rois:
            tr = self.get_roi_transform(roi)
            ishape = pg_roi_to_impose_shape(roi, tr, point_um=sl.point_um)
            sl.geometry[gid][0].__setstate__(ishape.__getstate__())
        self.structure_changed.emit()


class ColocPolyLineROI(pg.PolyLineROI):
    """A PolyLineROI that only allows for translation"""

    def __init__(self, **kw):
        if "points" not in kw:
            kw["points"] = [[10, 0], [10, 10], [0, 10]]
        super(ColocPolyLineROI, self).__init__(
            positions=np.array(kw["points"], copy=True), closed=True)

        self.sigRegionChangeStarted.connect(self.hide_handles)
        self.sigRegionChangeFinished.connect(self.hide_handles)

    def addFreeHandle(self, pos):
        """Override FreeHandle with TranslateHandle"""
        super(ColocPolyLineROI, self).addTranslateHandle(pos=pos)
        self.hide_handles()

    def setAngle(self, angle, center=None, centerLocal=None, snap=False,
                 update=True, finish=True):
        """Special override with rotation only around centerLocal"""
        if not angle:
            # This function is often called without an angle
            return
        assert centerLocal is not None
        assert center is None
        # Special case for polygons: We don't want to
        # set an angle to the ROI, because that makes
        # things more complicated when extracting the
        # array region (for once, the rotation center
        # is not known. I only planned the last line.
        centerLocal = pg.Point(centerLocal)
        points0 = np.array(self.getState()["points"])
        points = rotate_around_point(
            origin=(centerLocal.x(), centerLocal.y()),
            points=points0,
            angle=np.deg2rad(angle))
        self.setPoints(points, closed=True)

    def scale(self, s, center=None, centerLocal=None, snap=False, update=True,
              finish=True):
        """Special override with scale changed only around centerLocal"""
        if s == 1:
            return
        assert centerLocal is not None
        assert center is None
        points0 = np.array(self.getState()["points"])
        points0[:, 0] -= centerLocal.x()
        points0[:, 1] -= centerLocal.y()
        points = points0 * s
        points[:, 0] += centerLocal.x()
        points[:, 1] += centerLocal.y()
        self.setPoints(points, closed=True)

    def setSelected(self, s):
        self.hide_handles()

    @QtCore.pyqtSlot()
    def hide_handles(self):
        """Hide the handles, because we don't need any"""
        # hide handles
        for hh in self.handles:
            if hh["type"] == "t":
                # Hide polygon drag handles
                hh["item"].hide()
                hh["item"].setAcceptedMouseButtons(
                    QtCore.Qt.MouseButton.NoButton)

        for seg in self.segments:
            seg.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
            seg.setZValue(self.zValue() - 1000)

    def segmentClicked(self, segment, ev=None, pos=None):
        self.hide_handles()
