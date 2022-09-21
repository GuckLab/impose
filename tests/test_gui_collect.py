import pathlib

import numpy as np
from PyQt6 import QtCore, QtWidgets

from impose.gui.main import Impose

from helpers import retrieve_data


data_dir = pathlib.Path(__file__).parent / "data"


def test_basic(qtbot):
    """Run the program and exit"""
    mw = Impose()
    mw.close()


def test_load_bmlab_brillouin_data(qtbot, monkeypatch):
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022_water.zip")

    mw = Impose()
    qtbot.addWidget(mw)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileNames",
                        lambda *args: ([str(paths[0])], None))
    qtbot.mouseClick(mw.tab_collect.toolButton_add_data,
                     QtCore.Qt.MouseButton.LeftButton)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)

    # select the first entry in the datasets list (actual data)
    qtbot.mouseClick(mw.tab_collect.tableWidget_paths.cellWidget(0, 0),
                     QtCore.Qt.MouseButton.LeftButton)
    # sanity check (no data displayed)
    assert mw.tab_collect.groupBox_struct.isEnabled()

    # select the second entry in the visualization list
    item = mw.tab_collect.vis.listWidget_chan.item(1)
    item.setCheckState(QtCore.Qt.CheckState.Checked)
    assert mw.tab_collect.groupBox_struct.isEnabled()


def test_load_bmlab_brillouin_with_nan_data(qtbot, monkeypatch):
    paths = retrieve_data("fmt_brillouin-h5_bmlab-session_2022.zip")

    mw = Impose()
    qtbot.addWidget(mw)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileNames",
                        lambda *args: ([str(paths[0])], None))
    qtbot.mouseClick(mw.tab_collect.toolButton_add_data,
                     QtCore.Qt.MouseButton.LeftButton)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)

    # select the first entry in the datasets list (nan values)
    qtbot.mouseClick(mw.tab_collect.tableWidget_paths.cellWidget(0, 0),
                     QtCore.Qt.MouseButton.LeftButton)
    # sanity check (no data displayed)
    assert not mw.tab_collect.groupBox_struct.isEnabled()

    # select the second entry in the visualization list
    item = mw.tab_collect.vis.listWidget_chan.item(1)
    item.setCheckState(QtCore.Qt.CheckState.Checked)
    assert not mw.tab_collect.groupBox_struct.isEnabled()


def test_load_dataset(qtbot, monkeypatch):
    mw = Impose()
    qtbot.addWidget(mw)

    # Load example dataset
    example_data = data_dir / "brillouin.h5"
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileNames",
                        lambda *args: ([str(example_data)], None))
    qtbot.mouseClick(mw.tab_collect.toolButton_add_data,
                     QtCore.Qt.MouseButton.LeftButton)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 300)

    # make sure the data is loaded correctly
    assert len(mw.tab_collect.session_scheme.paths) == 1
    assert mw.tab_collect.session_scheme.paths[0].samefile(example_data)


def test_load_session(qtbot, monkeypatch):
    mw = Impose()
    qtbot.addWidget(mw)

    # Load example session
    example_session = data_dir / "brillouin.impose-session"
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *args: (str(example_session), None))
    mw.on_session_open()

    # select the first entry in the datasets list
    assert not mw.tab_collect.groupBox_struct.isEnabled()
    qtbot.mouseClick(mw.tab_collect.tableWidget_paths.cellWidget(0, 0),
                     QtCore.Qt.MouseButton.LeftButton)
    assert mw.tab_collect.groupBox_struct.isEnabled()

    # test a label
    label1 = mw.tab_collect.shape_control_widgets[0].comboBox_label
    assert label1.currentText() == "central canal"

    # test a structure layer
    sl = mw.tab_collect.current_structure_composite[0]
    assert sl.label == "central canal"
    assert sl.point_um == 2
    assert np.allclose(sl.position_um, [36.40899435294992 * 2,
                                        36.53086909469708 * 2])
