import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    # Start in a deliberate, centered desktop window instead of letting the
    # window manager choose an arbitrary position/size.
    screen = QGuiApplication.primaryScreen()
    if screen:
        available = screen.availableGeometry()
        width = min(1380, max(900, available.width() - 80))
        height = min(860, max(650, available.height() - 80))
        window.resize(width, height)
        window.move(
            available.x() + (available.width() - width) // 2,
            available.y() + (available.height() - height) // 2,
        )

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
