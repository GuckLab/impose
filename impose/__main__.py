def main():
    import os
    import pkg_resources
    import sys

    from PyQt6 import QtCore, QtGui, QtWidgets

    from impose.gui.main import Impose
    from impose._version import version as __version__

    for arg in sys.argv:
        if arg == '--version':
            print(__version__)
            sys.exit(0)

    # Set recursion limit to one million
    sys.setrecursionlimit(10 ** 6)

    # Starts the Impose application and handles its life cycle.
    app = QtWidgets.QApplication(sys.argv)
    # set window icon
    imdir = pkg_resources.resource_filename("impose", "img")
    icon_path = os.path.join(imdir, "icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))
    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.C))

    window = Impose()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    # Necessary to make multiprocessing work with pyinstaller
    from multiprocessing import freeze_support, set_start_method
    freeze_support()
    set_start_method('spawn')

    main()
