import shutil
import tempfile
import time

# register the mw fixture
from common_gui import mw


TMPDIR = tempfile.mkdtemp(prefix=time.strftime(
    "impose_test_%H.%M_"))


__all__ = ["mw"]

pytest_plugins = ["pytest-qt"]


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    tempfile.tempdir = TMPDIR


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    shutil.rmtree(TMPDIR, ignore_errors=True)
