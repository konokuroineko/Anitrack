from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ui.theme import COLORS, card_stylesheet, muted_label_stylesheet


class PersonCard(QFrame):
    clicked = Signal(object)

    def __init__(self, person, parent=None):
        super().__init__(parent)
        self.person = person
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(card_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.image = QLabel()
        self.image.setFixedSize(120, 120)
        self.image.setAlignment(Qt.AlignCenter)
        image_path = self._value("image_path")
        if image_path:
            self.image.setPixmap(QPixmap(image_path).scaled(
                self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        layout.addWidget(self.image, alignment=Qt.AlignCenter)

        name = QLabel(self._value("name") or "Unknown person")
        name.setWordWrap(True)
        name.setStyleSheet(f"color: {COLORS['primary']}; font-weight: 600;")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        role = self._value("role")
        if role:
            role_label = QLabel(role)
            role_label.setStyleSheet(muted_label_stylesheet())
            role_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(role_label)

    def _value(self, key):
        if hasattr(self.person, "get"):
            return self.person.get(key)
        try:
            return self.person[key]
        except (KeyError, TypeError):
            return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.person)
        super().mousePressEvent(event)
