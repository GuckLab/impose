import pathlib
import pkg_resources
import signal
import sys
import traceback

from PyQt6 import uic, QtCore, QtWidgets
import pyqtgraph as pg

from .widgets import ShowWaitCursor
from ..session import ImposeDataFileNotFoundError, ImposeSession
from .._version import version as __version__


pg.setConfigOption("background", "#F8F7DD")
pg.setConfigOption("foreground", "k")
pg.setConfigOption("antialias", True)
pg.setConfigOptions(imageAxisOrder="row-major")


class Impose(QtWidgets.QMainWindow):
    def __init__(self):
        # Settings are stored in the .ini file format. Even though
        # `self.settings` may return integer/bool in the same session,
        # in the next session, it will reliably return strings. Lists
        # of strings (comma-separated) work nicely though.
        QtCore.QCoreApplication.setOrganizationName("Impose")
        QtCore.QCoreApplication.setOrganizationDomain(
            "impose.readthedocs.io")
        QtCore.QCoreApplication.setApplicationName("impose")
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
        # Some promoted widgets may need the above constants set in order
        # to access the settings upon initialization.
        super(Impose, self).__init__()
        path_ui = pkg_resources.resource_filename("impose.gui", "main.ui")
        uic.loadUi(path_ui, self)
        self.setWindowTitle("impose {}".format(__version__))

        self.settings = QtCore.QSettings()

        self.session = ImposeSession()
        self.tab_collect.session_scheme = self.session.collect
        self.tab_coloc.session_scheme = self.session.colocalize

        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(QtCore.Qt.WindowState.WindowActive)

        # signals
        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        # clear stack
        self.actionClear.triggered.connect(self.on_session_clear)
        # open stack
        self.actionOpen.triggered.connect(self.on_session_open)
        # save stack
        self.actionSave.triggered.connect(self.on_session_save)

    @QtCore.pyqtSlot()
    def on_session_clear(self):
        self.session.clear()
        self.tab_collect.clear()
        self.tab_coloc.clear()

    @QtCore.pyqtSlot()
    def on_session_open(self):
        pdir = self.settings.value("path/session")
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open impose session", pdir, "*.impose-session")
        if path:
            self.settings.setValue("path/session",
                                   str(pathlib.Path(path).parent))
            self.on_session_clear()
            initial_dialog_shown = False
            search_paths = []
            while True:
                try:
                    with ShowWaitCursor():
                        self.session.load(path, search_paths=search_paths)
                except ImposeDataFileNotFoundError as e:
                    if not initial_dialog_shown:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Data file location unknown",
                            f"At least one file ({e.name}) could not be found "
                            "on this machine. In the following dialog(s), "
                            "please select the location(s) of the missing "
                            "file(s). The search is done recursively "
                            "(including subdirectories)."
                        )
                        initial_dialog_shown = True
                    # Let the user choose another search path
                    sdir = QtWidgets.QFileDialog.getExistingDirectory(
                        self,
                        f"Please select directory tree containing '{e.name}'!"
                    )
                    if sdir:
                        search_paths.append(sdir)
                    else:
                        # User pressed cancel
                        self.on_session_clear()
                        break
                else:
                    # All data files were found
                    self.tab_collect.update_ui_from_scheme()
                    self.tab_coloc.update_ui_from_scheme()
                    break

    @QtCore.pyqtSlot()
    def on_session_save(self):
        pdir = self.settings.value("path/session")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save session", pdir, "*.impose-session")
        if path:
            path = pathlib.Path(path)
            if not path.suffix == ".impose-session":
                path = path.with_name(path.name + ".impose-session")
            self.settings.setValue("path/session", str(path.parent))
            self.session.save(path)

    @QtCore.pyqtSlot(int)
    def on_tab_changed(self, index):
        """Update the composite stack for the new tab"""
        new = self.tabWidget.currentWidget()
        if new == self.tab_coloc:
            self.session.colocalize.update_composite_structures()
            self.tab_coloc.update_ui_from_scheme()


def excepthook(etype, value, trace):
    """
    Handler for all unhandled exceptions.

    :param `etype`: the exception type (`SyntaxError`,
        `ZeroDivisionError`, etc...);
    :type `etype`: `Exception`
    :param string `value`: the exception error message;
    :param string `trace`: the traceback header, if any (otherwise, it
        prints the standard Python header: ``Traceback (most recent
        call last)``.
    """
    vinfo = "Unhandled exception in Impose version {}:\n".format(
        __version__)
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join([vinfo]+tmp)

    errorbox = QtWidgets.QMessageBox()
    errorbox.addButton(QtWidgets.QPushButton('Close'),
                       QtWidgets.QMessageBox.ButtonRole.YesRole)
    errorbox.addButton(QtWidgets.QPushButton(
        'Copy text && Close'), QtWidgets.QMessageBox.ButtonRole.NoRole)
    errorbox.setText(exception)
    ret = errorbox.exec()
    if ret == 1:
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(exception)


# Make Ctr+C close the app
signal.signal(signal.SIGINT, signal.SIG_DFL)
# Display exception hook in separate dialog instead of crashing
sys.excepthook = excepthook
