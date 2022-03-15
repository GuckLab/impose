def main(splash=True):
    # import os
    # import pkg_resources
    import sys
    # import time

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
#    imdir = pkg_resources.resource_filename("impose", "img")

#    if splash:
#        from PyQt6.QtWidgets import QSplashScreen
#        from PyQt6.QtGui import QPixmap
#        splash_path = os.path.join(imdir, "splash.png")
#        splash_pix = QPixmap(splash_path)
#        splash = QSplashScreen(splash_pix)
#        splash.setMask(splash_pix.mask())
#        splash.show()
#        # make sure Qt really displays the splash screen
#        time.sleep(.07)
#        app.processEvents()

    from PyQt6 import QtCore  # , QtGui
    from .gui.main import Impose

#    # Set Application Icon
#    icon_path = os.path.join(imdir, "icon.png")
#    app.setWindowIcon(QtGui.QIcon(icon_path))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.C))

    window = Impose()  # noqa: F841

#    window = Impose()
#    if splash:
#        splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
