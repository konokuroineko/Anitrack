from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSpinBox, QVBoxLayout

from ui.theme import COLORS
from ui.widgets.progress_bar import ProgressBar


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
            QSpinBox {{ min-height: 28px; border-radius: 7px; }}
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

        title = QLabel(self._title())
        title.setObjectName("title")
        title.setWordWrap(True)
        title.setMaximumHeight(38)
        title.setToolTip(title.text())
        root.addWidget(title)

        meta_parts = []
        fmt = self._value("format")
        year = self._value("start_year")
        if not year:
            year = (self._value("startDate") or {}).get("year")
        if fmt:
            meta_parts.append(str(fmt).title())
        if year:
            meta_parts.append(str(year))
        score = self._value("averageScore")
        if mode == "search" and score:
            meta_parts.append(f"★ {score}")
        meta = QLabel("  ·  ".join(meta_parts))
        meta.setObjectName("meta")
        root.addWidget(meta)

        if mode == "search":
            add_button = QPushButton("+  Add to Library")
            add_button.setObjectName("add")
            add_button.setCursor(Qt.PointingHandCursor)
            add_button.clicked.connect(self._add_clicked)
            root.addWidget(add_button)
        else:
            progress = self._value("progress_episodes") or 0
            total = self._value("episodes") or 0
            if total or progress:
                root.addWidget(ProgressBar(progress, total))
                progress_label = QLabel(f"{progress} / {total}" if total else f"{progress} watched")
                progress_label.setObjectName("meta")
                root.addWidget(progress_label)
            if progress_editable:
                progress_box = QSpinBox()
                progress_box.setRange(0, total or 99999)
                progress_box.setValue(progress)
                progress_box.setPrefix("Episode  ")
                progress_box.valueChanged.connect(self.progress_changed)
                root.addWidget(progress_box)

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
        if reply is None:
            return
        if reply.error() == reply.NetworkError.NoError:
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._set_cover(pixmap)
        reply.deleteLater()

    def _set_cover(self, pixmap):
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
