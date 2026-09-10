from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout

from ui.theme import COLORS, card_stylesheet, muted_label_stylesheet


class RelationCard(QFrame):
    clicked = Signal(object)

    def __init__(self, relation, parent=None):
        super().__init__(parent)
        self.relation = relation
        self._network_manager = QNetworkAccessManager(self)
        self._cover_reply = None
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(card_stylesheet())

        layout = QHBoxLayout(self)
        self.image = QLabel()
        self.image.setFixedSize(60, 84)
        layout.addWidget(self.image)
        self._load_cover()

        text_layout = QVBoxLayout()
        title = QLabel(self._value("title") or "Unknown work")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-weight: 600;")
        title.setWordWrap(True)
        text_layout.addWidget(title)
        relation_type = (self._value("relation_type") or "Related").replace("_", " ").title()
        label = QLabel(relation_type)
        label.setStyleSheet(muted_label_stylesheet())
        text_layout.addWidget(label)
        text_layout.addStretch()
        layout.addLayout(text_layout)

    def _load_cover(self):
        image_path = self._value("cover_path")
        if image_path:
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                self._set_cover(pixmap)
                return

        image_url = self._value("cover_url")
        if not image_url:
            cover_image = self._value("coverImage") or {}
            image_url = cover_image.get("large")

        if image_url:
            self._cover_reply = self._network_manager.get(
                QNetworkRequest(QUrl(str(image_url)))
            )
            self._cover_reply.finished.connect(self._cover_finished)

    def _cover_finished(self):
        reply = self._cover_reply
        self._cover_reply = None
        if reply is None:
            return

        if reply.error() == reply.NetworkError.NoError:
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._set_cover(pixmap)
        reply.deleteLater()

    def _set_cover(self, pixmap):
        self.image.setPixmap(pixmap.scaled(
            self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

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
