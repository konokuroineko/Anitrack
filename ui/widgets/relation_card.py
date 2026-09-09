from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout

from ui.theme import COLORS, card_stylesheet, muted_label_stylesheet


class RelationCard(QFrame):
    clicked = Signal(object)

    def __init__(self, relation, parent=None):
        super().__init__(parent)
        self.relation = relation
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(card_stylesheet())

        layout = QHBoxLayout(self)
        image = QLabel()
        image.setFixedSize(60, 84)
        image_path = self._value("cover_path")
        if image_path:
            image.setPixmap(QPixmap(image_path).scaled(
                image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        layout.addWidget(image)

        text_layout = QVBoxLayout()
        title = QLabel(self._value("title") or "Unknown work")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-weight: 600;")
        text_layout.addWidget(title)
        relation_type = (self._value("relation_type") or "Related").replace("_", " ").title()
        label = QLabel(relation_type)
        label.setStyleSheet(muted_label_stylesheet())
        text_layout.addWidget(label)
        text_layout.addStretch()
        layout.addLayout(text_layout)

    def _value(self, key):
        if hasattr(self.relation, "get"):
            return self.relation.get(key)
        try:
            return self.relation[key]
        except (IndexError, KeyError, TypeError):
            return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.relation)
        super().mousePressEvent(event)
