import pathlib

import numpy as np
from PyQt6 import QtCore, QtWidgets

from impose.gui.main import Impose

data_dir = pathlib.Path(__file__).parent / "data"


def test_basic(qtbot):
    """Run the program and exit"""
    mw = Impose()
    mw.close()


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
    assert not mw.tab_collect.widget_struct.isEnabled()
    qtbot.mouseClick(mw.tab_collect.tableWidget_paths.cellWidget(0, 0),
                     QtCore.Qt.MouseButton.LeftButton)
    assert mw.tab_collect.widget_struct.isEnabled()

    # test a label
    label1 = mw.tab_collect.shape_control_widgets[0].comboBox_label
    assert label1.currentText() == "central canal"

    # test a structure layer
    sl = mw.tab_collect.current_structure_composite[0]
    assert sl.label == "central canal"
    assert sl.point_um == 2
    assert np.allclose(sl.position_um, [36.40899435294992 * 2,
                                        36.53086909469708 * 2])
