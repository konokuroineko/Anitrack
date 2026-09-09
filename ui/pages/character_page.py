from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CharacterPage(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Character"))
        layout.addStretch()
