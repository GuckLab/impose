def main(splash=True):
    # import os
    # import pkg_resources
    import sys
    # import time

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
#    imdir = pkg_resources.resource_filename("impose", "img")

    from PyQt6 import QtCore  # , QtGui
    from .gui.main import Impose

#    # Set Application Icon
#    icon_path = os.path.join(imdir, "icon.png")
#    app.setWindowIcon(QtGui.QIcon(icon_path))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.C))

    window = Impose()  # noqa: F841

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
