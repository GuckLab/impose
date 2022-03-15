import pkg_resources

import numpy as np
from PyQt6 import uic, QtWidgets


class EditDialog(QtWidgets.QDialog):
    def __init__(self, ui_name, shape, *args, **kwargs):
        super(EditDialog, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("impose.gui", ui_name)
        uic.loadUi(path_ui, self)
        self.shape = shape
        self.point_um = shape.point_um

        # Dialog box buttons
        btn_apply = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok)
        btn_apply.clicked.connect(self.on_ok)


class EditCircleDialog(EditDialog):
    def __init__(self, *args, **kwargs):
        super(EditCircleDialog, self).__init__("dlg_edit_circle.ui",
                                               *args, **kwargs)
        self.doubleSpinBox_radius.setValue(self.shape.r * self.point_um)
        self.doubleSpinBox_x.setValue(self.shape.x * self.point_um)
        self.doubleSpinBox_y.setValue(self.shape.y * self.point_um)

    def on_ok(self):
        self.shape.r = self.doubleSpinBox_radius.value() / self.point_um
        self.shape.x = self.doubleSpinBox_x.value() / self.point_um
        self.shape.y = self.doubleSpinBox_y.value() / self.point_um


class EditEllipseDialog(EditDialog):
    def __init__(self, *args, **kwargs):
        super(EditEllipseDialog, self).__init__("dlg_edit_ellipse.ui",
                                                *args, **kwargs)
        self.doubleSpinBox_a.setValue(self.shape.a * self.point_um)
        self.doubleSpinBox_b.setValue(self.shape.b * self.point_um)
        self.doubleSpinBox_phi.setValue(np.rad2deg(self.shape.phi))
        self.doubleSpinBox_x.setValue(self.shape.x * self.point_um)
        self.doubleSpinBox_y.setValue(self.shape.y * self.point_um)

    def on_ok(self):
        self.shape.a = self.doubleSpinBox_a.value() / self.point_um
        self.shape.b = self.doubleSpinBox_b.value() / self.point_um
        self.shape.phi = np.deg2rad(self.doubleSpinBox_phi.value())
        self.shape.x = self.doubleSpinBox_x.value() / self.point_um
        self.shape.y = self.doubleSpinBox_y.value() / self.point_um


class EditPolygonDialog(EditDialog):
    def __init__(self, *args, **kwargs):
        super(EditPolygonDialog, self).__init__("dlg_edit_polygon.ui",
                                                *args, **kwargs)
        points = np.array(self.shape.points) * self.point_um
        self.tableWidget.setRowCount(len(points))
        for ii, (x, y) in enumerate(points):
            spinx = QtWidgets.QDoubleSpinBox(self)
            spiny = QtWidgets.QDoubleSpinBox(self)
            for sp in [spinx, spiny]:
                sp.setMinimum(-1e9)
                sp.setMaximum(1e9)
            spinx.setValue(x)
            spiny.setValue(y)
            self.tableWidget.setCellWidget(ii, 0, spinx)
            self.tableWidget.setCellWidget(ii, 1, spiny)

    def on_ok(self):
        points = []
        for ii in range(self.tableWidget.rowCount()):
            x = self.tableWidget.cellWidget(ii, 0).value()
            y = self.tableWidget.cellWidget(ii, 1).value()
            points.append([x, y])
        self.shape.points[:] = np.array(points) / self.point_um


class EditRectangleDialog(EditDialog):
    def __init__(self, *args, **kwargs):
        super(EditRectangleDialog, self).__init__("dlg_edit_rectangle.ui",
                                                  *args, **kwargs)
        self.doubleSpinBox_a.setValue(self.shape.a * self.point_um)
        self.doubleSpinBox_b.setValue(self.shape.b * self.point_um)
        self.doubleSpinBox_phi.setValue(np.rad2deg(self.shape.phi))
        self.doubleSpinBox_x.setValue(self.shape.x * self.point_um)
        self.doubleSpinBox_y.setValue(self.shape.y * self.point_um)

    def on_ok(self):
        self.shape.a = self.doubleSpinBox_a.value() / self.point_um
        self.shape.b = self.doubleSpinBox_b.value() / self.point_um
        self.shape.phi = np.deg2rad(self.doubleSpinBox_phi.value())
        self.shape.x = self.doubleSpinBox_x.value() / self.point_um
        self.shape.y = self.doubleSpinBox_y.value() / self.point_um


def dialog_for_shape(shape, *args, **kwargs):
    sdict = {
        "Circle": EditCircleDialog,
        "Ellipse": EditEllipseDialog,
        "Polygon": EditPolygonDialog,
        "Rectangle": EditRectangleDialog,
    }
    dlg = sdict[shape.__class__.__name__](shape, *args, **kwargs)
    return dlg
