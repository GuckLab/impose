import pathlib

from PyQt6 import QtWidgets


data_dir = pathlib.Path(__file__).parent / "data"


def test_load_session(mw, qtbot, monkeypatch):
    # Load example session
    example_session = data_dir / "brillouin.impose-session"
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName",
                        lambda *args: (str(example_session), None))
    mw.on_session_open()

    # make sure that the path is loaded correctly
    assert mw.tab_coloc.tableWidget_paths.rowCount() == 1
