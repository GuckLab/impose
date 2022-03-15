from collections import OrderedDict
import copy
import pkg_resources

import numpy as np
from PyQt6 import uic, QtCore, QtWidgets


class Visualize(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        """Everything concerning image visualization"""
        super(Visualize, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("impose.gui", "visualize.ui")
        uic.loadUi(path_ui, self)

        # current data source
        self._data_source = None

        # initially hide bar (rest is done via ui file)
        self.widget_bar.setHidden(True)

        # signals
        # user changes view slice
        self.slider_slice.valueChanged.connect(self.on_view_slice_changed)
        # user changes view plane
        self.comboBox_plane.currentTextChanged.connect(
            self.on_view_plane_changed)
        # user changed blend mode
        self.comboBox_blend.currentTextChanged.connect(self.update_image)
        # user changed channel index
        self.listWidget_chan.itemClicked.connect(self.on_channel_selected)
        self.listWidget_chan.itemChanged.connect(self.on_channel_selected)
        self.listWidget_chan.itemChanged.connect(self.update_image)
        # user changed channel color
        self.slider_hue.valueChanged.connect(self.update_image)
        # user changed brightness
        self.slider_brightness.valueChanged.connect(self.update_image)
        # user changed contrast
        self.slider_contrast.valueChanged.connect(self.update_image)

    def __getstate__(self):
        """Get metadata from UI, compatible with DataSource.metadata"""
        ds = self.data_source
        # view plane
        plane = self.comboBox_plane.currentText()
        pld = {"x-y": ([0, 1], 2),
               "y-z": ([1, 2], 0),
               "z-x": ([0, 2], 1),
               }
        # view slice
        cslice = self.slider_slice.value()
        cut_axis_size = ds.shape[pld[plane][1]]
        if cslice >= cut_axis_size:
            cslice = cut_axis_size // 2
        # channel metadata
        meta_channels = OrderedDict()
        for name in ds.metadata["channels"]:
            chd = copy.deepcopy(ds.metadata["channels"][name])
            meta_channels[name] = chd
        # get current channel
        row = self.listWidget_chan.currentRow()
        if row >= 0:
            cname = list(meta_channels.keys())[row]
            # set color
            meta_channels[cname]["hue"] = self.slider_hue.value()
            meta_channels[cname]["brightness"] = self.slider_brightness.value()
            meta_channels[cname]["contrast"] = self.slider_contrast.value()
        # get selected channels (checkboxes in list)
        channels_sel = []
        for ii, cname in enumerate(meta_channels):
            qwi = self.listWidget_chan.item(ii)
            if qwi.checkState() == QtCore.Qt.CheckState.Checked:
                channels_sel.append(cname)

        state = {
            "blend": {
                "mode": self.comboBox_blend.currentText().lower(),
                "channels": channels_sel,
            },
            "channels": meta_channels,
            "slice": {
                "view plane": pld[plane][0],
                "cut axis": pld[plane][1],
                "view slice": cslice,
            },
            "stack": ds.metadata["stack"],
        }
        return state

    def __setstate__(self, state):
        """Set UI elements from a state

        It is assumed that self.data_source is set correctly.
        """
        # TODO
        # - blend mode

        # channel options
        self.listWidget_chan.blockSignals(True)
        # clear list widget
        for _ in range(self.listWidget_chan.count()):
            self.listWidget_chan.takeItem(0)
        # add channels
        for name in state["channels"]:
            qwi = QtWidgets.QListWidgetItem(name)
            qwi.setFlags(qwi.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            if name in state["blend"]["channels"]:
                qwi.setCheckState(QtCore.Qt.CheckState.Checked)
            else:
                qwi.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.listWidget_chan.addItem(qwi)
        self.listWidget_chan.setCurrentRow(0)
        self.listWidget_chan.blockSignals(False)
        # Update color sliders
        self.on_channel_selected()

        # view plane
        pld = {2: "x-y",
               0: "y-z",
               1: "z-x"}
        self.comboBox_plane.blockSignals(True)
        self.comboBox_plane.setCurrentText(
            pld[state["slice"]["cut axis"]])
        self.comboBox_plane.blockSignals(False)
        # view slice
        self.update_slider_maximum(state)
        self.update_label_slice(state)
        self.slider_slice.blockSignals(True)
        self.slider_slice.setValue(state["slice"]["view slice"])
        self.slider_slice.blockSignals(False)
        self.update_image()

    @property
    def data_source(self):
        """The current :class:`impose.data.DataSource` instance"""
        return self._data_source

    def clear(self):
        """Reset to initial state"""
        self._data_source = None
        self.listWidget_chan.clear()
        self.imageView.clear()
        self.setEnabled(False)

    def get_roi_transform(self, roi):
        """Return transform from ROI to data coordinates"""
        # get the image item
        img = self.imageView.getImageItem()
        # get the raw data
        data = np.array(self.imageView.image)[:, :, 0]
        # transform for mapping from geometry to data coordinates
        _, tr = roi.getArraySlice(data, img)
        return tr

    @QtCore.pyqtSlot()
    def on_channel_selected(self):
        """User changed channel, populate color options

        There is no need to update the image here.
        """
        ds = self.data_source
        index = self.listWidget_chan.currentRow()
        # color button
        item = list(ds.metadata["channels"].values())[index]
        self.slider_hue.blockSignals(True)
        self.slider_hue.setValue(item["hue"])
        self.slider_hue.blockSignals(False)
        # brightness slider
        self.slider_brightness.blockSignals(True)
        self.slider_brightness.setValue(item["brightness"])
        self.slider_brightness.blockSignals(False)
        # contrast slider
        self.slider_contrast.blockSignals(True)
        self.slider_contrast.setValue(item["contrast"])
        self.slider_contrast.blockSignals(False)

    @QtCore.pyqtSlot()
    def on_view_plane_changed(self):
        """The user changed the view plane

        This implies updating the maximum value of the slice slider.
        """
        self.update_slider_maximum()
        self.update_image()

    @QtCore.pyqtSlot()
    def on_view_slice_changed(self):
        """The user changed the view slice

        Update `label_slice`.
        """
        self.update_label_slice()
        self.update_image()

    def set_data_source(self, data_source):
        """Populates UI with dataset settings"""
        # save the current state in the old data source
        if self._data_source is not None:
            self._data_source.update_metadata(self.__getstate__())
        # replace the current data source
        self._data_source = data_source
        # set the metadata in the UI
        self.__setstate__(data_source.metadata)
        # finally update the image
        self.update_image(override_metadata=False)
        # hide slicing options if 2d source
        if len(self.data_source.shape) == 2:
            self.groupBox_slicing.setVisible(False)
        else:
            self.groupBox_slicing.setVisible(True)

    @QtCore.pyqtSlot()
    def update_image(self, override_metadata=True):
        """Redraw the image

        If `override_metadata` is True (default), then the
        metadata of the underlying DataSource is modified
        (This is a convenience method so that this function
        can be a slot for the various controls).
        """
        ds = self.data_source
        if override_metadata:
            ds.update_metadata(self.__getstate__())
        image = ds.get_image()
        sx, sy = ds.get_pixel_size()
        # Scaling/Normalization to the x-axis pixel size (y is scaled).
        self.imageView.setImage(image,
                                scale=[1, sx/sy],
                                autoRange=False,
                                autoLevels=False)

    def update_label_slice(self, state=None):
        """Update label_slice"""
        if state is None:
            state = self.__getstate__()
        index = state["slice"]["view slice"]
        label = "{}".format(index)
        step_um = self.data_source.get_voxel_depth()
        if step_um is not None and not np.isnan(step_um):
            label += " ({:.1f} µm)".format(index * step_um)
        self.label_slice.setText(label)

    def update_slider_maximum(self, state=None):
        """Update the slice slider maximum

        If not state is given (e.g. from a DataSource.metadata),
        then the current state of the UI is used to determine
        the maximum value allowed.
        """
        if state is None:
            state = self.__getstate__()
        cut_axis = state["slice"]["cut axis"]
        cut_axis_size = state["stack"]["shape"][cut_axis]
        self.slider_slice.blockSignals(True)
        self.slider_slice.setMaximum(cut_axis_size-1)
        self.slider_slice.blockSignals(False)
