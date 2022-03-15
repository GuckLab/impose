import json
import pathlib
import pkg_resources

import numpy as np
from PyQt6 import uic, QtCore, QtWidgets

from .. import formats

from .colocalize_pgrois import StructureCompositeGroupedROIs


class Colocalize(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(Colocalize, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("impose.gui",
                                                  "colocalize.ui")
        uic.loadUi(path_ui, self)

        # Hide initially (visibility handled in .ui file)
        self.widget_draw_and_fit.setVisible(False)

        #: Current session scheme is set in main (instance of
        #: :class:`impose.session.ImposeSessionSchemeColocalize`);
        #: This is populated in `main`.
        self.session_scheme = None

        #: list of currently active ROIs
        self.rois = StructureCompositeGroupedROIs(
            image_view=self.vis.imageView)

        self.settings = QtCore.QSettings()

        self._prev_rotate = 0
        self._prev_translate_x = 0
        self._prev_translate_y = 0

        # disable widget for shape controls initially
        self.widget_struct.setEnabled(False)
        self.vis.setEnabled(False)

        for tab in [self.tableWidget_paths, self.tableWidget_structures]:
            header = tab.horizontalHeader()
            header.setSectionResizeMode(
                0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(
                0, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Tool Button Add Menu
        # options button
        # TODO: populate with correct labels
        # menu = QtWidgets.QMenu()
        # menu.addAction('label name', self.on_structure_add)

        # signals
        # user wants to add new dataset(s)
        self.toolButton_add_data.clicked.connect(self.on_add_data)
        # user selects new item
        self.tableWidget_paths.cellClicked.connect(self.on_dataset_selected)
        # the ROI was changed
        self.rois.structure_changed.connect(self.update_statistics)
        self.rois.structure_changed.connect(self.update_structure_layer_view)
        self.comboBox_channel.currentIndexChanged.connect(
            self.update_structure_layer_view)
        # the user wants to export structure data
        self.toolButton_export.clicked.connect(self.on_export_tsv)
        # translation and rotation
        self.dial_translatex.valueChanged.connect(self.on_translate_x)
        self.dial_translatey.valueChanged.connect(self.on_translate_y)
        self.dial_rotate.valueChanged.connect(self.on_rotate)

    @property
    def current_data_source(self):
        row = self.tableWidget_paths.currentRow()
        ds = self.session_scheme.data_sources[row]
        return ds

    @property
    def current_point_um(self):
        return self.current_data_source.get_pixel_size()[0]

    @property
    def current_structure_composite(self):
        row = self.tableWidget_paths.currentRow()
        if self.mode == "manual":
            sc = self.session_scheme.strucure_composites_manual[row]
        else:
            raise NotImplementedError("Introduce new structure!")
        return sc

    @property
    def mode(self):
        if self.radioButton_manual.isChecked:
            mode = "manual"
        else:
            mode = "draw and fit"
        return mode

    @property
    def viewbox(self):
        """Viewbox of `self.vis`"""
        return self.vis.imageView.getView()

    def add_paths(self, paths):
        for pp in paths:
            self.session_scheme.append(pp)
        self.update_table_paths()

    def clear(self):
        self.session_scheme.clear()
        self.rois.clear()

        self.tableWidget_paths.clearContents()
        self.tableWidget_paths.setRowCount(0)
        self.tableWidget_structures.clearContents()
        self.tableWidget_structures.setRowCount(0)
        self.imageViewROI.clear()
        self.comboBox_channel.blockSignals(True)
        self.comboBox_channel.clear()
        self.comboBox_channel.blockSignals(False)
        self.vis.clear()

    def get_structure_layer_data(self, structure_layer=None, flatten=True):
        """Return the data points enclosed by the ROI

        Parameters
        ----------
        structure_layer: impose.structure.StructureLayer
            Structure from which to extract the data; defaults to
            self.rois.active_structure_layer
        flatten: bool
            If False, return an image with points outside the ROI
            set to nan. If True (default), return a flattened array
            of the ROI data points.
        """
        # obtain the current (sliced) 2D raw data from the data source
        channel = self.comboBox_channel.currentData()
        data = self.current_data_source.get_channel_data(channel)
        # obtain the image mask using
        # - the current data_source shape and pixel sizes and
        # - the currently active structure layer
        if structure_layer is None:
            structure_layer = self.rois.active_structure_layer
        mask = structure_layer.to_mask(self.current_data_source)
        if flatten:
            return data[mask]
        else:
            # Remove all zeros from the mask that are not essential
            # for visualization.
            if np.sum(mask):
                ii, jj = np.where(mask)
                indices = np.meshgrid(np.arange(min(ii), max(ii) + 1),
                                      np.arange(min(jj), max(jj) + 1),
                                      indexing='ij')
                # get subimage
                data_roi = np.array(data[tuple(indices)], dtype=float)
                mask_roi = mask[tuple(indices)]
                # apply mask to subimage
                data_roi[~mask_roi] = np.nan
            else:
                data_roi = np.nan * np.zeros((2, 2))
            return data_roi

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
        """User clicked on a dataset/path

        - Update the visible shapes in self.vis
        - Update the structure table
        """
        if self.current_structure_composite:
            self.widget_struct.setEnabled(True)
            self.vis.setEnabled(True)
            # set available channels in ROI visualization
            self.comboBox_channel.blockSignals(True)
            for _ in range(self.comboBox_channel.count()):
                self.comboBox_channel.removeItem(0)
            for key in list(self.current_data_source.data_channels.keys()):
                self.comboBox_channel.addItem(key, key)
            self.comboBox_channel.blockSignals(False)
            self.update_ui_from_scheme()
        else:
            self.widget_struct.setEnabled(False)
            self.vis.setEnabled(False)
            self.rois.clear()

    @QtCore.pyqtSlot()
    def on_export_tsv(self):
        # file open dialog
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Export directory", self.settings.value("path/export_tsv"))
        if not path:
            return
        self.settings.setValue("path/export_tsv", path)
        # data save stem
        ds = self.current_data_source
        sc = self.current_structure_composite
        stem = ds.path.stem
        data = sc.extract_data(ds)
        for ll in data:
            layd = data[ll]
            # export all channel data as a text file
            lp = pathlib.Path(path) / "{}_{}.tsv".format(stem, ll)
            channels = sorted(layd.keys())
            # data
            layarr = np.zeros((layd[channels[0]].size, len(channels)),
                              dtype=float)
            for ii, chn in enumerate(channels):
                layarr[:, ii] = layd[chn]
            np.savetxt(lp, layarr,
                       fmt="%.5g",
                       delimiter="\t",
                       header="\t".join(channels),
                       newline="\r\n",
                       encoding="utf-8",
                       )
        # also save the structure composite
        pc = pathlib.Path(path) / "{}.impose-composite".format(stem)
        with pc.open("w") as fd:
            json.dump(sc.__getstate__(), fd,
                      ensure_ascii=False,
                      allow_nan=True,
                      indent=1,
                      sort_keys=False)

    @QtCore.pyqtSlot(int)
    def on_rotate(self, phi_int):
        dphi = (phi_int / 5000 - .5) * 2 * np.pi
        rotate_diff = dphi - self._prev_rotate
        self._prev_rotate = dphi
        self.current_structure_composite.rotate(rotate_diff)
        self.rois.update_roi_geometry()

    @QtCore.pyqtSlot(int)
    def on_translate_x(self, trx_int):
        trlx = (trx_int / 5000) - .5
        trlx_diff = self._prev_translate_x - trlx
        if trlx_diff > .4:
            trlx_diff -= 1
        if trlx_diff < -.4:
            trlx_diff += 1
        self._prev_translate_x = trlx
        self.current_structure_composite.translate(
            (-trlx_diff/self.current_point_um*42, 0))
        self.rois.update_roi_geometry()

    @QtCore.pyqtSlot(int)
    def on_translate_y(self, try_int):
        trly = (try_int / 5000) - .5
        trly_diff = self._prev_translate_y - trly
        if trly_diff > .4:
            trly_diff -= 1
        if trly_diff < -.4:
            trly_diff += 1
        self._prev_translate_y = trly
        self.current_structure_composite.translate(
            (0, trly_diff/self.current_point_um*42))
        self.rois.update_roi_geometry()

    @QtCore.pyqtSlot()
    def update_statistics(self):
        if self.session_scheme.data_sources:
            for row, sl in enumerate(self.current_structure_composite):
                data = self.get_structure_layer_data(sl, flatten=True)
                wmean = self.tableWidget_structures.item(row, 1)
                wmean.setText("{:.4g}".format(np.nanmean(data)))

    @QtCore.pyqtSlot()
    def update_structure_layer_view(self):
        data = self.get_structure_layer_data(flatten=False)
        if data.size == 0 or np.all(np.isnan(data)):
            data = np.zeros((2, 2))
        self.imageViewROI.setImage(data)
        self.imageViewROI.autoRange()

    def update_structure_table(self):
        """Updates tableWidget_structures"""
        sc = self.session_scheme.scs.get_mean()
        self.tableWidget_structures.setRowCount(len(sc))
        # populate self.tableWidget_structures
        for ii, sl in enumerate(sc):
            wlabel = self.tableWidget_structures.cellWidget(ii, 0)
            wmean = self.tableWidget_structures.item(ii, 1)
            if wlabel is None:
                # create all widgets
                wlabel = QtWidgets.QLabel(sl.label)
                self.tableWidget_structures.setCellWidget(ii, 0, wlabel)
                wmean = QtWidgets.QTableWidgetItem("--")
                self.tableWidget_structures.setItem(ii, 1, wmean)
            else:
                wlabel.setText(sl.label)
            chex = "#{:02X}{:02X}{:02X}".format(*list(sl.color)[:3])
            wlabel.setStyleSheet("background-color: " + chex + ";")

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
        """Updates UI with information from self.session_scheme"""
        if self.session_scheme.paths:
            # list of paths
            self.update_table_paths()
            # list of shapes
            self.update_structure_table()
            # set new ROIs
            self.vis.set_data_source(self.current_data_source)
            self.rois.set_structure_composite(self.current_structure_composite,
                                              self.vis)
