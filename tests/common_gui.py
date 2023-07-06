import time

import pytest
from PyQt6 import QtCore, QtWidgets, QtTest

from impose.gui.main import Impose


@pytest.fixture
def mw(qtbot):
    # Always set server correctly, because there is a test that
    # makes sure DCOR-Aid starts with a wrong server.
    QtCore.QCoreApplication.setOrganizationName("Impose")
    QtCore.QCoreApplication.setOrganizationDomain(
        "impose.readthedocs.io")
    QtCore.QCoreApplication.setApplicationName("impose")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    # settings = QtCore.QSettings()
    # settings.setIniCodec("utf-8")
    QtTest.QTest.qWait(100)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 5000)
    # Code that will run before your test
    mw = Impose()
    qtbot.addWidget(mw)
    QtWidgets.QApplication.setActiveWindow(mw)
    QtTest.QTest.qWait(100)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 5000)
    # Run test
    yield mw
    # Make sure that all daemons are gone
    mw.close()
    # It is extremely weird, but this seems to be important to avoid segfaults!
    time.sleep(1)
    QtTest.QTest.qWait(100)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 5000)
