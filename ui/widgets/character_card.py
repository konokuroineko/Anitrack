from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout

from ui.theme import COLORS, card_stylesheet, muted_label_stylesheet


class CharacterCard(QFrame):
    clicked = Signal(object)

    def __init__(self, character, parent=None):
        super().__init__(parent)
        self.character = character
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(card_stylesheet())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        image = QLabel()
        image.setFixedSize(72, 96)
        image.setAlignment(Qt.AlignCenter)
        image_path = self._value("character_image_path")
        if image_path:
            image.setPixmap(QPixmap(image_path).scaled(
                image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        layout.addWidget(image)

        text_layout = QVBoxLayout()
        name = QLabel(self._value("character_name") or "Unknown character")
        name.setWordWrap(True)
        name.setStyleSheet(f"color: {COLORS['primary']}; font-weight: 600;")
        text_layout.addWidget(name)

        person_name = self._value("person_name")
        if person_name:
            voice = QLabel(f"Voice: {person_name}")
            voice.setWordWrap(True)
            voice.setStyleSheet(muted_label_stylesheet())
            text_layout.addWidget(voice)
        text_layout.addStretch()
        layout.addLayout(text_layout)

    def _value(self, key):
        if hasattr(self.character, "get"):
            return self.character.get(key)
        try:
            return self.character[key]
        except (KeyError, TypeError):
            return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.character)
        super().mousePressEvent(event)
