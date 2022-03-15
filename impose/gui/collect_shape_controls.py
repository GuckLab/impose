import pkg_resources

from PyQt6 import uic, QtCore, QtWidgets

from . import dlg_edit_shape


class CollectShapeControls(QtWidgets.QWidget):
    instances = []
    color_changed = QtCore.pyqtSignal()
    shape_changed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(CollectShapeControls, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("impose.gui",
                                                  "collect_shape_controls.ui")
        uic.loadUi(path_ui, self)

        # initial variables
        self.structure_composite = None
        self.structure_layer = None
        self.geometry_index = None

        # signal color changed
        self.toolButton_color.sigColorChanged.connect(self.on_color_changed)
        self.toolButton_color.sigColorChanging.connect(self.on_color_changed)
        # signal delete
        self.toolButton_delete.clicked.connect(self.on_shape_delete)
        # signal edit
        self.toolButton_shape.clicked.connect(self.on_shape_edit)
        # label edit
        self.comboBox_label.currentIndexChanged.connect(self.on_layer_changed)
        # use lineEdit so that currentIndexChanged is not triggered
        self.comboBox_label.lineEdit().textEdited.connect(
            self.on_label_changed)
        # cast edit
        self.spinBox_cast.valueChanged.connect(self.on_cast_changed)

        CollectShapeControls.instances.append(self)

    @QtCore.pyqtSlot()
    def on_color_changed(self):
        color = self.toolButton_color.color(mode="byte")
        self.structure_layer.color = color
        # update the color for all other layers
        for other in CollectShapeControls.instances:
            if other is self:
                continue
            elif other.structure_layer is self.structure_layer:
                other.toolButton_color.blockSignals(True)
                other.toolButton_color.setColor(color)
                other.toolButton_color.blockSignals(False)
        self.color_changed.emit()

    @QtCore.pyqtSlot(int)
    def on_cast_changed(self, cast):
        geometry = self.structure_layer.geometry
        current_geometry = list(geometry[self.geometry_index])
        current_geometry[1] = cast
        geometry[self.geometry_index] = tuple(current_geometry)

    @QtCore.pyqtSlot(str)
    def on_label_changed(self, new_label):
        old_label = self.structure_layer.label
        try:
            self.structure_composite.change_layer_label(
                old_label, new_label)
        except ValueError:
            # not allowed
            self.comboBox_label.blockSignals(True)
            self.comboBox_label.setCurrentText(old_label)
            self.comboBox_label.blockSignals(False)
        # update the label for all other layers
        for inst in CollectShapeControls.instances:
            inst.update_layer_labels()

    @QtCore.pyqtSlot(int)
    def on_layer_changed(self, index):
        """Move the shape to a different layer"""
        # remove from current layer
        geom = self.structure_layer.geometry.pop(self.geometry_index)
        # add to new layer
        new_layer = self.structure_composite[index]
        new_layer.geometry.append(geom)
        self.remove_empty_layers()
        self.shape_changed.emit()

    @QtCore.pyqtSlot()
    def on_shape_delete(self):
        self.structure_layer.geometry.pop(self.geometry_index)
        self.remove_empty_layers()
        self.shape_changed.emit()

    @QtCore.pyqtSlot()
    def on_shape_edit(self):
        # get shape
        shape = self.structure_layer.geometry[self.geometry_index][0]
        # The dialog edits the shape in-place
        dlg = dlg_edit_shape.dialog_for_shape(shape, self)
        dlg.exec_()
        self.shape_changed.emit()

    def remove_empty_layers(self):
        for sl in reversed(self.structure_composite):
            if len(sl.geometry) == 0:
                # remove empty layer from structure
                self.structure_composite.remove(sl)

    def update_layer_labels(self):
        self.comboBox_label.blockSignals(True)
        self.comboBox_label.clear()
        if self.structure_layer in self.structure_composite:
            # This only makes sense if the current layer still exists
            layer_index = self.structure_composite.index(self.structure_layer)
            for sli in self.structure_composite:
                self.comboBox_label.addItem(sli.label, sli)
            self.comboBox_label.setCurrentIndex(layer_index)
        self.comboBox_label.blockSignals(False)

    def set_shape(self, structure_composite, layer_label, geometry_index):
        sl = structure_composite[layer_label]
        layer_index = structure_composite.index(sl)
        self.structure_composite = structure_composite
        self.structure_layer = sl
        self.geometry_index = geometry_index
        # set layer label
        self.update_layer_labels()
        # set layer index
        self.label_layer_index.setText(f"{layer_index}")
        # set color
        self.toolButton_color.blockSignals(True)
        self.toolButton_color.setColor(sl.color)
        self.toolButton_color.blockSignals(False)
        # set shape-edit button text and tool tip
        state = sl.__getstate__()
        label_dict = {"Circle": "○",
                      "Ellipse": "⬭",
                      "Rectangle": "▭",
                      "Polygon": "⭔",
                      }
        shape_name = state["geometry"][geometry_index][0]
        shape_label = label_dict[shape_name]
        self.toolButton_shape.setText(shape_label)
        self.toolButton_shape.setToolTip(f'edit {shape_name.lower()}')
        # set casting value
        shape_cast = state["geometry"][geometry_index][2]
        self.spinBox_cast.setValue(shape_cast)
