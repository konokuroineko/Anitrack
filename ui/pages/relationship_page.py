from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class RelationshipPage(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Relationships"))
        layout.addStretch()
