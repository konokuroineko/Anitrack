import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.preferences import get


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    if get("maximized"):
        window.showMaximized()
    else:
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
