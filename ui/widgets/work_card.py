from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ui.theme import (
    COLORS,
    SPACING,
    muted_label_stylesheet,
)

from ui.widgets.progress_bar import ProgressBar


class WorkCard(QFrame):

    clicked = Signal(object)
    progress_changed = Signal(int)
    add_requested = Signal(object)

    def __init__(
        self,
        work,
        progress_editable=False,
        mode="library",
        add_callback=None,
        parent=None
    ):
        super().__init__(parent)

        self.work = work
        self.mode = mode
        self.add_callback = add_callback
        self._network_manager = QNetworkAccessManager(self)
        self._cover_reply = None

        self.setObjectName("workCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(206)
        self.setMinimumHeight(345)
        self.setStyleSheet(f"""
            QFrame#workCard {{
                background: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame#workCard:hover {{
                background: {COLORS['card_hover']};
                border-color: {COLORS['border_hover']};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
            QPushButton {{
                border-radius: 7px;
                padding: 7px 10px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        shadow.setColor(Qt.black)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 13)
        layout.setSpacing(8)

        self.cover = QLabel()
        self.cover.setFixedSize(180, 250)
        self.cover.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cover, alignment=Qt.AlignCenter)
        self._load_cover()

        title = QLabel(self._title())
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignLeft)
        title.setMaximumHeight(42)
        title.setToolTip(title.text())
        title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: 13px;
            font-weight: 700;
        """)
        layout.addWidget(title)

        subtitle = self._subtitle()
        if mode == "search":
            score = self._value("averageScore")
            if score:
                subtitle = f"{subtitle} • Score: {score}" if subtitle else f"Score: {score}"

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(muted_label_stylesheet())
            layout.addWidget(subtitle_label)

        progress = self._value("progress_episodes")
        total = self._value("episodes")

        if mode == "search":
            add_button = QPushButton("+  Add to Library")
            add_button.setCursor(Qt.PointingHandCursor)
            add_button.clicked.connect(self._add_clicked)
            layout.addWidget(add_button)
        elif progress is not None or total is not None:
            progress_value = progress or 0
            total_value = total or 0
            progress_bar = ProgressBar(progress_value, total_value)
            layout.addWidget(progress_bar)
            progress_label = QLabel(
                f"{progress_value} / {total_value}" if total_value else f"{progress_value} watched"
            )
            progress_label.setStyleSheet(muted_label_stylesheet())
            layout.addWidget(progress_label)

            if progress_editable:
                progress_box = QSpinBox()
                progress_box.setRange(0, total_value or 99999)
                progress_box.setValue(progress_value)
                progress_box.setPrefix("Episode ")
                progress_box.setCursor(Qt.PointingHandCursor)
                progress_box.valueChanged.connect(self.progress_changed)
                layout.addWidget(progress_box)

        layout.addStretch()

    def _load_cover(self):
        cover_path = self._value("cover_path")
        if cover_path:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                self._set_cover(pixmap)
                return

        cover_url = self._value("cover_url")
        if not cover_url:
            cover_image = self._value("coverImage") or {}
            cover_url = cover_image.get("large")

        if cover_url:
            self._cover_reply = self._network_manager.get(
                QNetworkRequest(QUrl(str(cover_url)))
            )
            self._cover_reply.finished.connect(self._cover_finished)

    def _cover_finished(self):
        reply = self._cover_reply
        self._cover_reply = None
        if reply is None:
            return

        if reply.error() == reply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self._set_cover(pixmap)
        reply.deleteLater()

    def _set_cover(self, pixmap):
        self.cover.setPixmap(pixmap.scaled(
            self.cover.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

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

    def _subtitle(self):
        start_year = self._value("start_year")
        if not start_year:
            start_date = self._value("startDate") or {}
            start_year = start_date.get("year")
        parts = [self._value("format"), start_year]
        return " • ".join(str(part) for part in parts if part)

    def _title(self):
        title = self._value("title")
        if isinstance(title, dict):
            return title.get("english") or title.get("romaji") or title.get("native") or "Untitled"
        return title or "Untitled"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.work)
        super().mousePressEvent(event)
