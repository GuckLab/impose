def main():
    import os
    import pkg_resources
    import sys
    import logging

    from PyQt6 import QtGui, QtWidgets

    from impose.gui.main import Impose
    from impose._version import version as __version__
    """
    Starts the Impose application and handles its life cycle.
    """
    app = QtWidgets.QApplication(sys.argv)
    # set window icon
    imdir = pkg_resources.resource_filename("impose", "img")
    icon_path = os.path.join(imdir, "icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    window = Impose()
    window.show()

    for arg in sys.argv:
        if arg == '--version':
            print(__version__)
            QtWidgets.QApplication.processEvents()
            sys.exit(0)
        elif arg.startswith('--log='):
            log_level = arg[6:]
            logging.basicConfig(level=log_level)

    sys.exit(app.exec())


if __name__ == '__main__':
    # Necessary to make multiprocessing work with pyinstaller
    from multiprocessing import freeze_support, set_start_method
    freeze_support()
    set_start_method('spawn')

    main()
