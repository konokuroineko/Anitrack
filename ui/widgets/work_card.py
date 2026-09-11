from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QPen, QColor
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QSizePolicy

from database import save_cover_path
from ui.theme import COLORS


IMAGE_DIRECTORY = Path("data") / "images" / "works"


class CoverFrame(QFrame):
    """Poster with artwork clipped to the rounded frame and an orange outline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setFixedSize(210, 284)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        rect = self.rect().adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(rect, 11, 11)
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (scaled.width() - rect.width()) // 2)
            y = max(0, (scaled.height() - rect.height()) // 2)
            cropped = scaled.copy(x, y, rect.width(), rect.height())
            painter.save()
            painter.setClipPath(path)
            painter.drawPixmap(rect.topLeft(), cropped)
            painter.restore()
        painter.setPen(QPen(QColor(COLORS["accent"]), 3.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.end()


class WorkCard(QFrame):
    clicked = Signal(object)
    progress_changed = Signal(int)
    add_requested = Signal(object)

    _cover_cache = {}
    _cover_failures = set()

    def __init__(self, work, progress_editable=False, mode="library", add_callback=None, parent=None):
        super().__init__(parent)
        self.work = work
        self.mode = mode
        self.add_callback = add_callback
        self._network_manager = QNetworkAccessManager(self)
        self._cover_reply = None
        self.setObjectName("posterCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(210)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame#posterCard {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 13px;
                padding: 6px;
            }}
            QFrame#posterCard:hover {{
                background: {COLORS['surface']};
                border-color: {COLORS['border_hover']};
            }}
            QLabel {{ background: transparent; border: none; }}
            QLabel#title {{ color: {COLORS['primary']}; font-size: 13px; font-weight: 760; }}
            QFrame#posterCard:hover QLabel#title {{ color: {COLORS['accent_hover']}; }}
            QLabel#meta {{ color: {COLORS['muted']}; font-size: 11px; }}
            QPushButton#add {{ background: {COLORS['accent']}; color: #111318; border: none; border-radius: 8px; padding: 7px; font-weight: 800; }}
            QPushButton#add:hover {{ background: {COLORS['accent_hover']}; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        self.cover = CoverFrame()
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
                self.cover.set_pixmap(pixmap)
                return

        cover_url = self._value("cover_url") or (self._value("coverImage") or {}).get("large")
        if not cover_url:
            return
        cover_url = str(cover_url)

        cached = self._cover_cache.get(cover_url)
        if cached is not None and not cached.isNull():
            self.cover.set_pixmap(cached)
            return
        if cover_url in self._cover_failures:
            return

        self._cover_reply = self._network_manager.get(QNetworkRequest(QUrl(cover_url)))
        self._cover_reply.finished.connect(lambda: self._cover_finished(cover_url))

    def _cover_finished(self, cover_url):
        reply = self._cover_reply
        self._cover_reply = None
        if reply is not None and reply.error() == reply.NetworkError.NoError:
            pixmap = QPixmap()
            if pixmap.loadFromData(reply.readAll()):
                self._cover_cache[cover_url] = pixmap
                self.cover.set_pixmap(pixmap)
                work_id = self._value("id")
                if work_id:
                    try:
                        IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
                        path = IMAGE_DIRECTORY / f"{work_id}.jpg"
                        if pixmap.save(str(path), "JPG", 85):
                            save_cover_path(work_id, str(path))
                    except Exception:
                        pass
            else:
                self._cover_failures.add(cover_url)
        else:
            self._cover_failures.add(cover_url)
        if reply is not None:
            reply.deleteLater()

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
