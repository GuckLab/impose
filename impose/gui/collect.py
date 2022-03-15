import pathlib
import pkg_resources

import numpy as np
from PyQt6 import uic, QtCore, QtWidgets
from skimage.color import hsv2rgb

from .. import formats
from ..geometry import shapes
from ..structure import StructureLayer

from .collect_pgrois import StructureCompositeROIs
from .collect_shape_controls import CollectShapeControls


class Collect(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(Collect, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("impose.gui", "collect.ui")
        uic.loadUi(path_ui, self)

        #: Current session scheme is set in main (instance of
        #: :class:`impose.session.ImposeSessionSchemeCollect`);
        #: This is populated in `main`.
        self.session_scheme = None

        #: A helper class that handles all ROIs and the modification of
        #: the current StructureComposite
        self.sc_rois = StructureCompositeROIs(image_view=self.vis.imageView)

        self.settings = QtCore.QSettings()

        #: A list holding all instances of CollectShapeControls
        self.shape_control_widgets = []

        # disable widget for shape controls initially
        self.widget_struct.setEnabled(False)
        self.vis.setEnabled(False)

        # set horizontal stretch for path list
        header = self.tableWidget_paths.horizontalHeader()
        header.setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0,
                                    QtWidgets.QHeaderView.ResizeMode.Stretch)

        # signal for user wants to add new dataset(s)
        self.toolButton_add_data.clicked.connect(self.on_add_data)
        # signal for user selects new item
        self.tableWidget_paths.cellClicked.connect(self.on_dataset_selected)
        # signals for tool button shapes
        self.toolButton_add_circle.clicked.connect(self.on_shape_add_circle)
        self.toolButton_add_ellipse.clicked.connect(self.on_shape_add_ellipse)
        self.toolButton_add_polygon.clicked.connect(self.on_shape_add_polygon)
        self.toolButton_add_rectangle.clicked.connect(
            self.on_shape_add_rectangle)

    @property
    def current_data_source(self):
        """Currently selected DataSource"""
        row = self.tableWidget_paths.currentRow()
        ds = self.session_scheme.data_sources[row]
        return ds

    @property
    def current_point_um(self):
        return self.current_data_source.get_pixel_size()[0]

    @property
    def current_structure_composite(self):
        """Currently active StructureComposite"""
        row = self.tableWidget_paths.currentRow()
        sc = self.session_scheme.scs[row]
        return sc

    def add_paths(self, paths):
        for pp in paths:
            self.session_scheme.append(pp)
        self.update_table_paths()

    def add_shape(self, shape_cls):
        # instantiate a shape
        ishape = shape_cls(point_um=self.current_point_um)
        # set size to 1/3rd of image size
        imsize = max(self.current_data_source.get_image_size_um())
        ishape.set_size(max(round(imsize/5), 1))
        cs = self.current_structure_composite
        # get valid label name
        ii = len(cs)
        while True:
            label = "label-{}".format(ii + 1)
            if label in cs:
                ii += 1
            else:
                break
        sl = StructureLayer(label=label,
                            geometry=[(ishape, 1)],
                            point_um=self.current_point_um,
                            color=random_color(),
                            )
        cs.append(sl)
        self.sc_rois.update_pg_rois()
        self.update_shape_list()

    def clear(self):
        """Reset the UI to its initial state"""
        self.session_scheme.clear()
        self.sc_rois.clear()
        self.clear_shape_list()
        self.tableWidget_paths.clearContents()
        self.tableWidget_paths.setRowCount(0)
        self.vis.clear()

    def clear_shape_list(self):
        self.shape_control_widgets.clear()
        for ii in reversed(range(self.verticalLayout_structures.count())):
            item = self.verticalLayout_structures.itemAt(ii)
            if item.widget() is None:
                self.verticalLayout_structures.removeItem(item)
            else:
                item.widget().setParent(None)

    @QtCore.pyqtSlot()
    def on_add_data(self):
        suffixes = [f"*{suf}" for suf in formats.suffix_dict.keys()]
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Data file", self.settings.value("path/import"),
            f"Supported formats ({' '.join(suffixes)})")

        if paths:
            self.settings.setValue("path/import",
                                   str(pathlib.Path(paths[0]).parent))

        self.add_paths(paths)

    @QtCore.pyqtSlot()
    def on_dataset_selected(self):
        """Populates UI with dataset settings"""
        self.widget_struct.setEnabled(True)
        self.vis.setEnabled(True)
        self.vis.set_data_source(self.current_data_source)
        self.update_shape_list()
        self.sc_rois.set_structure_composite(self.current_structure_composite)

    @QtCore.pyqtSlot()
    def on_layer_color_changed(self):
        """The color of a layer changed"""
        # update the color of the pg ROIs
        self.sc_rois.update_roi_colors()

    @QtCore.pyqtSlot()
    def on_layer_shape_changed(self):
        """The shape of a layer changed (or was deleted)"""
        self.sc_rois.update_pg_rois()
        self.update_shape_list()

    @QtCore.pyqtSlot()
    def on_shape_add_circle(self):
        self.add_shape(shapes.Circle)

    @QtCore.pyqtSlot()
    def on_shape_add_ellipse(self):
        self.add_shape(shapes.Ellipse)

    @QtCore.pyqtSlot()
    def on_shape_add_polygon(self):
        self.add_shape(shapes.Polygon)

    @QtCore.pyqtSlot()
    def on_shape_add_rectangle(self):
        self.add_shape(shapes.Rectangle)

    @QtCore.pyqtSlot()
    def update_shape_list(self):
        """Populate self.widget_structures"""
        self.widget_structures.setUpdatesEnabled(False)
        # First, clear the layout
        self.clear_shape_list()
        # Then, populate with current composite structure
        sc = self.current_structure_composite
        for ii, sl in enumerate(sc):
            for jj in range(len(sl.geometry)):
                # get the current item
                wopts = CollectShapeControls(self)
                self.verticalLayout_structures.addWidget(wopts)
                wopts.set_shape(structure_composite=sc,
                                layer_label=sl.label,
                                geometry_index=jj)
                wopts.color_changed.connect(self.on_layer_color_changed)
                wopts.shape_changed.connect(self.on_layer_shape_changed)
                self.shape_control_widgets.append(wopts)

        # Finally add a stretch spacer in case there are not enough
        # items.
        spacer_item = QtWidgets.\
            QSpacerItem(20, 0,
                        QtWidgets.QSizePolicy.Policy.Minimum,
                        QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_structures.addItem(spacer_item)
        self.widget_structures.setUpdatesEnabled(True)

    def update_table_paths(self):
        paths = self.session_scheme.paths
        self.tableWidget_paths.setRowCount(len(paths))
        for row, pp in enumerate(paths):
            for jj, label in enumerate([str(pp), str(row + 1)]):
                # set pseudo-right elided text with dots on left
                item = self.tableWidget_paths.item(row, jj)
                if item is None:
                    # create widget if it does not exist
                    item = QtWidgets.QLabel()
                    self.tableWidget_paths.setCellWidget(row, jj, item)
                QtWidgets.QApplication.processEvents(
                    QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 500)
                f_metrics = item.fontMetrics()
                s = item.size().width() - 5
                ellabel = f_metrics.elidedText(
                    label, QtCore.Qt.TextElideMode.ElideLeft, s)
                item.setText(ellabel)

    def update_ui_from_scheme(self):
        # list of paths
        self.update_table_paths()
        # list of layers
        self.update_shape_list()
        # set new ROIs
        self.vis.set_data_source(self.current_data_source)
        self.sc_rois.set_structure_composite(self.current_structure_composite)


def random_color():
    hue = np.random.rand()
    rgb = hsv2rgb([hue, .5, 1])
    return np.array(rgb*255, dtype=int).tolist()
