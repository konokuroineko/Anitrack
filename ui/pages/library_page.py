from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from database import get_all_library, update_library_progress
from ui.theme import COLORS, SPACING, muted_label_stylesheet
from ui.widgets.work_card import WorkCard


class LibraryPage(QWidget):
    """A status-specific collection page.

    The old combined Library view is intentionally gone from the navigation.
    Each instance represents exactly one status: Watching, Completed, or Planned.
    """

    work_selected = Signal(object)

    STATUS_MAP = {
        "Watching": "Watching",
        "Completed": "Completed",
        "Planned": "Planning",
    }

    def __init__(self, status="Watching"):
        super().__init__()
        self.status = status if status in self.STATUS_MAP else "Watching"
        self.all_anime = []
        self.anime_list = []
        self.current_sort = "Recently Added"
        self.grid_container = None
        self.grid_layout = None
        self.scroll_area = None
        self.sort_box = None
        self.refresh()

    def refresh(self):
        self.all_anime = list(get_all_library())
        wanted_status = self.STATUS_MAP[self.status]
        self.anime_list = [
            anime for anime in self.all_anime
            if anime["status"] == wanted_status
        ]
        self._apply_sort()
        self._build_page()

    def _apply_sort(self):
        if self.current_sort == "Title":
            self.anime_list.sort(key=lambda anime: (anime["title"] or "").lower())
        elif self.current_sort == "Release Year":
            self.anime_list.sort(
                key=lambda anime: anime["start_year"] or 0,
                reverse=True,
            )
        elif self.current_sort == "Recently Added":
            self.anime_list.sort(key=lambda anime: anime["id"], reverse=True)

    def _build_page(self):
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        else:
            old_layout = QVBoxLayout(self)

        old_layout.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        old_layout.setSpacing(SPACING["md"])

        title_row = QHBoxLayout()
        title_column = QVBoxLayout()

        title = QLabel(self.status)
        title.setStyleSheet(
            f"font-size: 30px; font-weight: 750; color: {COLORS['primary']};"
        )
        subtitle = QLabel(self._subtitle())
        subtitle.setStyleSheet(muted_label_stylesheet())
        title_column.addWidget(title)
        title_column.addWidget(subtitle)
        title_row.addLayout(title_column)
        title_row.addStretch()

        sort_label = QLabel("Sort")
        sort_label.setStyleSheet(muted_label_stylesheet())
        title_row.addWidget(sort_label)

        self.sort_box = QComboBox()
        self.sort_box.setFixedWidth(150)
        self.sort_box.addItems(["Recently Added", "Title", "Release Year"])
        self.sort_box.setCurrentText(self.current_sort)
        self.sort_box.currentTextChanged.connect(self._sort_changed)
        title_row.addWidget(self.sort_box)
        old_layout.addLayout(title_row)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        old_layout.addWidget(divider)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 8, 4, 8)
        self.grid_layout.setHorizontalSpacing(SPACING["lg"])
        self.grid_layout.setVerticalSpacing(SPACING["xl"])
        self.scroll_area.setWidget(self.grid_container)
        old_layout.addWidget(self.scroll_area, 1)

        self._populate_grid()

    def _subtitle(self):
        count = len(self.anime_list)
        if count == 1:
            return "1 title"
        return f"{count} titles"

    def _populate_grid(self):
        if not self.grid_layout:
            return

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.anime_list:
            empty = QWidget()
            empty_layout = QVBoxLayout(empty)
            empty_layout.setAlignment(Qt.AlignCenter)

            icon = QLabel("✦")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet(f"color: {COLORS['accent']}; font-size: 42px;")

            message = QLabel(f"Nothing in {self.status.lower()} yet")
            message.setAlignment(Qt.AlignCenter)
            message.setStyleSheet(
                f"color: {COLORS['primary']}; font-size: 22px; font-weight: 700;"
            )

            prompt = QLabel(
                "Search for something to add to your collection."
            )
            prompt.setAlignment(Qt.AlignCenter)
            prompt.setStyleSheet(muted_label_stylesheet())

            empty_layout.addWidget(icon)
            empty_layout.addWidget(message)
            empty_layout.addWidget(prompt)
            self.grid_layout.addWidget(empty, 0, 0)
            return

        columns = self._column_count()
        for index, anime in enumerate(self.anime_list):
            card = WorkCard(anime, progress_editable=True)
            card.clicked.connect(self.work_selected)
            card.progress_changed.connect(
                lambda value, work_id=anime["id"]: update_library_progress(
                    work_id, episodes=value
                )
            )
            self.grid_layout.addWidget(card, index // columns, index % columns)

        for column in range(columns):
            self.grid_layout.setColumnStretch(column, 1)

    def _column_count(self):
        if not self.scroll_area:
            return 1
        card_width = 206 + SPACING["lg"]
        available = self.scroll_area.viewport().width()
        return max(1, available // card_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._populate_grid()

    def _sort_changed(self, sort_name):
        self.current_sort = sort_name
        self._apply_sort()
        self._populate_grid()
