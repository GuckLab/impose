import os

os.environ["PYQTGRAPH_QT_LIB"] = "PyQt6"

# flake8: noqa: F401
from . import geometry
from . import structure
from ._version import version as __version__
