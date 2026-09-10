from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from database import get_all_library, update_library_progress
from ui.theme import COLORS, SPACING
from ui.widgets.work_card import WorkCard


class LibraryPage(QWidget):
    work_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.all_anime = []
        self.anime_list = []
        self.current_filter = "All"
        self.current_sort = "Recently Added"
        self.grid_layout = None
        self.scroll_area = None
        self.filter_box = None
        self.sort_box = None
        self._build_shell()
        self.refresh()

    def _build_shell(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        root.setSpacing(SPACING["lg"])

        header = QHBoxLayout()
        title = QLabel("Library")
        title.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {COLORS['primary']};")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(SPACING["sm"])
        status_label = QLabel("Status")
        status_label.setStyleSheet(f"color: {COLORS['muted']}; font-weight: 600;")
        toolbar.addWidget(status_label)
        self.filter_box = QComboBox()
        self.filter_box.addItems(["All", "Watching", "Completed", "Planned"])
        self.filter_box.setFixedWidth(145)
        self.filter_box.currentTextChanged.connect(self._filter_changed)
        toolbar.addWidget(self.filter_box)
        toolbar.addSpacing(10)
        sort_label = QLabel("Sort")
        sort_label.setStyleSheet(f"color: {COLORS['muted']}; font-weight: 600;")
        toolbar.addWidget(sort_label)
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Recently Added", "Title", "Release Year"])
        self.sort_box.setFixedWidth(165)
        self.sort_box.currentTextChanged.connect(self._sort_changed)
        toolbar.addWidget(self.sort_box)
        toolbar.addStretch()
        root.addLayout(toolbar)

        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {COLORS['border']};")
        root.addWidget(line)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setContentsMargins(0, 4, 0, 4)
        self.grid_layout.setHorizontalSpacing(SPACING["lg"])
        self.grid_layout.setVerticalSpacing(SPACING["xl"])
        self.scroll_area.setWidget(container)
        root.addWidget(self.scroll_area, 1)

    def refresh(self):
        self.all_anime = list(get_all_library())
        self._apply_filter()
        self._apply_sort()
        self._populate()

    def _apply_filter(self):
        wanted = {"All": None, "Watching": "Watching", "Completed": "Completed", "Planned": "Planning"}[self.current_filter]
        self.anime_list = [x for x in self.all_anime if wanted is None or x["status"] == wanted]

    def _apply_sort(self):
        if self.current_sort == "Title":
            self.anime_list.sort(key=lambda x: (x["title"] or "").lower())
        elif self.current_sort == "Release Year":
            self.anime_list.sort(key=lambda x: x["start_year"] or 0, reverse=True)
        else:
            self.anime_list.sort(key=lambda x: x["id"], reverse=True)

    def _filter_changed(self, value):
        self.current_filter = value
        self._apply_filter()
        self._apply_sort()
        self._populate()

    def _sort_changed(self, value):
        self.current_sort = value
        self._apply_sort()
        self._populate()

    def _populate(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.anime_list:
            empty = QLabel("No titles in this view")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {COLORS['muted']}; font-size: 17px; padding: 80px;")
            self.grid_layout.addWidget(empty, 0, 0)
            return
        columns = max(1, self.scroll_area.viewport().width() // 224)
        for index, anime in enumerate(self.anime_list):
            card = WorkCard(anime, progress_editable=True)
            card.clicked.connect(self.work_selected)
            card.progress_changed.connect(lambda value, work_id=anime["id"]: update_library_progress(work_id, episodes=value))
            self.grid_layout.addWidget(card, index // columns, index % columns)
        for col in range(columns):
            self.grid_layout.setColumnStretch(col, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._populate()
