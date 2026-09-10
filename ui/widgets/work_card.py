from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from ui.theme import COLORS


class WorkCard(QFrame):
    clicked = Signal(object)
    progress_changed = Signal(int)
    add_requested = Signal(object)

    def __init__(self, work, progress_editable=False, mode="library", add_callback=None, parent=None):
        super().__init__(parent)
        self.work = work
        self.mode = mode
        self.add_callback = add_callback
        self._network_manager = QNetworkAccessManager(self)
        self._cover_reply = None
        self.setObjectName("posterCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(202)
        self.setStyleSheet(f"""
            QFrame#posterCard {{ background: transparent; border: none; }}
            QFrame#posterCard:hover QLabel#coverFrame {{ border: 2px solid {COLORS['accent']}; }}
            QLabel {{ background: transparent; border: none; }}
            QLabel#coverFrame {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}
            QLabel#title {{ color: {COLORS['primary']}; font-size: 13px; font-weight: 760; }}
            QLabel#meta {{ color: {COLORS['muted']}; font-size: 11px; }}
            QPushButton#add {{ background: {COLORS['accent']}; color: #111318; border: none; border-radius: 8px; padding: 7px; font-weight: 800; }}
            QPushButton#add:hover {{ background: {COLORS['accent_hover']}; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.cover = QLabel()
        self.cover.setObjectName("coverFrame")
        self.cover.setFixedSize(202, 276)
        self.cover.setAlignment(Qt.AlignCenter)
        root.addWidget(self.cover)
        self._load_cover()

        # The library card is intentionally information-light. Episode controls
        # belong to the title's detail page, not on top of the library grid.
        if mode == "library":
            progress = self._value("progress_episodes") or 0
            total = self._value("episodes") or 0
            if total and progress > 0:
                line = QFrame(self.cover)
                line.setObjectName("progressLine")
                width = 202 if progress >= total else max(3, int(202 * progress / total))
                line.setGeometry(0, 268, width, 8)
                line.setStyleSheet(f"QFrame#progressLine {{ background:{COLORS['accent']}; border:0; border-radius:0 0 9px 9px; }}")

        title = QLabel(self._title())
        title.setObjectName("title")
        title.setWordWrap(True)
        title.setMaximumHeight(38)
        title.setToolTip(title.text())
        root.addWidget(title)

        meta_parts = []
        fmt = self._value("format")
        year = self._value("start_year") or (self._value("startDate") or {}).get("year")
        if fmt:
            meta_parts.append(str(fmt).title())
        if year:
            meta_parts.append(str(year))
        score = self._value("averageScore")
        if mode == "search" and score:
            meta_parts.append(f"★ {score}")
        if meta_parts:
            meta = QLabel("  ·  ".join(meta_parts))
            meta.setObjectName("meta")
            root.addWidget(meta)

        if mode == "search":
            add_button = QPushButton("+  Add to Library")
            add_button.setObjectName("add")
            add_button.setCursor(Qt.PointingHandCursor)
            add_button.clicked.connect(self._add_clicked)
            root.addWidget(add_button)

    def _load_cover(self):
        cover_path = self._value("cover_path")
        if cover_path:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                self._set_cover(pixmap)
                return
        cover_url = self._value("cover_url") or (self._value("coverImage") or {}).get("large")
        if cover_url:
            self._cover_reply = self._network_manager.get(QNetworkRequest(QUrl(str(cover_url))))
            self._cover_reply.finished.connect(self._cover_finished)

    def _cover_finished(self):
        reply = self._cover_reply
        self._cover_reply = None
        if reply is not None and reply.error() == reply.NetworkError.NoError:
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._set_cover(pixmap)
        if reply is not None:
            reply.deleteLater()

    def _set_cover(self, pixmap):
        # Keep the full artwork visible so the accent line always has a stable edge.
        self.cover.setPixmap(pixmap.scaled(self.cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _add_clicked(self):
        self.add_requested.emit(self.work)
        if self.add_callback:
            self.add_callback(self.work, self.sender())

    def _value(self, key):
        if hasattr(self.work, "get"):
            return self.work.get(key)
        try:
            return self.work[key]
        except (KeyError, TypeError, IndexError):
            return None

    def _title(self):
        title = self._value("title")
        if isinstance(title, dict):
            return title.get("english") or title.get("romaji") or title.get("native") or "Untitled"
        return title or "Untitled"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.work)
            return
        super().mousePressEvent(event)
