from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

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
        root.setContentsMargins(34, 30, 34, 28)
        root.setSpacing(18)

        top = QHBoxLayout()
        top.setSpacing(14)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Library")
        title.setStyleSheet(f"font-size: 32px; font-weight: 850; color: {COLORS['primary']};")
        self.count_label = QLabel("0 titles")
        self.count_label.setStyleSheet(f"font-size: 12px; color: {COLORS['muted']};")
        title_box.addWidget(title)
        title_box.addWidget(self.count_label)
        top.addLayout(title_box)
        top.addStretch()
        root.addLayout(top)

        controls = QFrame()
        controls.setStyleSheet(f"QFrame {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 14px; }}")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 8, 10, 8)
        controls_layout.setSpacing(7)

        self.filter_buttons = {}
        for label in ["All", "Watching", "Completed", "Planned"]:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, value=label: self._set_filter(value))
            self.filter_buttons[label] = button
            controls_layout.addWidget(button)

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        controls_layout.addWidget(divider)

        sort_text = QLabel("SORT")
        sort_text.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {COLORS['muted']}; letter-spacing: 1px;")
        controls_layout.addWidget(sort_text)
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Recently Added", "Title", "Release Year"])
        self.sort_box.setMinimumWidth(150)
        self.sort_box.currentTextChanged.connect(self._sort_changed)
        controls_layout.addWidget(self.sort_box)
        controls_layout.addStretch()
        root.addWidget(controls)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setContentsMargins(4, 12, 4, 20)
        self.grid_layout.setHorizontalSpacing(22)
        self.grid_layout.setVerticalSpacing(30)
        self.scroll_area.setWidget(container)
        root.addWidget(self.scroll_area, 1)

        self._set_filter("All")

    def refresh(self):
        self.all_anime = list(get_all_library())
        self._apply_filter()
        self._apply_sort()
        self._populate()

    def _set_filter(self, value):
        self.current_filter = value
        for name, button in self.filter_buttons.items():
            button.setChecked(name == value)
            button.setStyleSheet(self._filter_style(name == value))
        self._apply_filter()
        self._apply_sort()
        self._populate()

    def _filter_style(self, active):
        if active:
            return f"QPushButton {{ background: {COLORS['accent']}; color: #101216; border: none; border-radius: 9px; padding: 8px 15px; font-weight: 800; }}"
        return f"QPushButton {{ background: transparent; color: {COLORS['secondary']}; border: none; border-radius: 9px; padding: 8px 15px; font-weight: 650; }} QPushButton:hover {{ background: {COLORS['surface_hover']}; color: {COLORS['primary']}; }}"

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

    def _sort_changed(self, value):
        self.current_sort = value
        self._apply_sort()
        self._populate()

    def _populate(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.count_label.setText(f"{len(self.anime_list)} title{'s' if len(self.anime_list) != 1 else ''}")
        if not self.anime_list:
            empty = QFrame()
            empty.setStyleSheet(f"background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 18px;")
            box = QVBoxLayout(empty)
            box.setContentsMargins(30, 50, 30, 50)
            icon = QLabel("○")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet(f"font-size: 34px; color: {COLORS['accent']}; border: none;")
            text = QLabel("Nothing here yet")
            text.setAlignment(Qt.AlignCenter)
            text.setStyleSheet(f"font-size: 17px; font-weight: 750; color: {COLORS['primary']}; border: none;")
            hint = QLabel("Add titles from Search and they will appear in your library.")
            hint.setAlignment(Qt.AlignCenter)
            hint.setStyleSheet(f"font-size: 12px; color: {COLORS['muted']}; border: none;")
            box.addWidget(icon)
            box.addWidget(text)
            box.addWidget(hint)
            self.grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        columns = max(1, self.scroll_area.viewport().width() // 230)
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
