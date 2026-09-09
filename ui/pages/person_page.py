from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PersonPage(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Person"))
        layout.addStretch()
