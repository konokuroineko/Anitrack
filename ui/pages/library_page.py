from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from database import get_all_library
from ui.theme import COLORS
from ui.widgets.work_card import WorkCard


class LibraryPage(QWidget):
    work_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.all_anime = []
        self.anime_list = []
        self.current_filter = "All"
        self.current_sort = "Recently Added"
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(120)
        self._resize_timer.timeout.connect(self._reflow_grid)
        self._build_shell()
        self.refresh()

    def _build_shell(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(38, 32, 38, 30)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_box = QVBoxLayout(); title_box.setSpacing(2)
        title = QLabel("Library")
        title.setStyleSheet(f"font-size:32px;font-weight:850;color:{COLORS['primary']};")
        self.count_label = QLabel("0 titles")
        self.count_label.setStyleSheet(f"font-size:12px;color:{COLORS['muted']};")
        title_box.addWidget(title); title_box.addWidget(self.count_label)
        header.addLayout(title_box); header.addStretch()
        root.addLayout(header)

        controls = QFrame()
        controls.setStyleSheet(f"QFrame{{background:{COLORS['surface']};border:1px solid {COLORS['border']};border-radius:14px;}}")
        row = QHBoxLayout(controls); row.setContentsMargins(9, 8, 9, 8); row.setSpacing(6)
        self.filter_buttons = {}
        for name in ["All", "Watching", "Completed", "Planned"]:
            b = QPushButton(name); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked=False, value=name: self._set_filter(value))
            self.filter_buttons[name] = b; row.addWidget(b)
        divider = QFrame(); divider.setFixedWidth(1); divider.setStyleSheet(f"background:{COLORS['border']};border:0;")
        row.addWidget(divider)
        label = QLabel("SORT"); label.setStyleSheet(f"font-size:10px;font-weight:800;color:{COLORS['muted']};letter-spacing:1px;")
        row.addWidget(label)
        self.sort_box = QComboBox(); self.sort_box.addItems(["Recently Added", "Title", "Release Year"]); self.sort_box.setMinimumWidth(150)
        self.sort_box.currentTextChanged.connect(self._sort_changed); row.addWidget(self.sort_box); row.addStretch()
        root.addWidget(controls)

        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True); self.scroll_area.setFrameShape(QFrame.NoFrame); self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container = QWidget(); self.grid_layout = QGridLayout(container)
        self.grid_layout.setContentsMargins(4, 10, 4, 20)
        self.grid_layout.setHorizontalSpacing(24)
        self.grid_layout.setVerticalSpacing(30)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_area.setWidget(container); root.addWidget(self.scroll_area, 1)
        self._set_filter("All")

    def refresh(self):
        self.all_anime = list(get_all_library()); self._apply_filter(); self._apply_sort(); self._populate()

    def _set_filter(self, value):
        self.current_filter = value
        for name, button in self.filter_buttons.items():
            button.setChecked(name == value); button.setStyleSheet(self._filter_style(name == value))
        self._apply_filter(); self._apply_sort(); self._populate()

    def _filter_style(self, active):
        if active:
            return f"QPushButton{{background:{COLORS['accent']};color:#101216;border:0;border-radius:9px;padding:8px 15px;font-weight:800;}}"
        return f"QPushButton{{background:transparent;color:{COLORS['secondary']};border:0;border-radius:9px;padding:8px 15px;font-weight:650;}}QPushButton:hover{{background:{COLORS['surface_hover']};color:{COLORS['primary']};}}"

    def _apply_filter(self):
        wanted = {"All":None,"Watching":"Watching","Completed":"Completed","Planned":"Planning"}[self.current_filter]
        self.anime_list = [x for x in self.all_anime if wanted is None or x["status"] == wanted]

    def _apply_sort(self):
        if self.current_sort == "Title": self.anime_list.sort(key=lambda x:(x["title"] or "").lower())
        elif self.current_sort == "Release Year": self.anime_list.sort(key=lambda x:x["start_year"] or 0, reverse=True)
        else: self.anime_list.sort(key=lambda x:x["id"], reverse=True)

    def _sort_changed(self, value):
        self.current_sort = value; self._apply_sort(); self._populate()

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _column_count(self):
        card_width = 210
        column_gap = 24
        available_width = max(0, self.scroll_area.viewport().width() - 8)
        return max(1, (available_width + column_gap) // (card_width + column_gap))

    def _populate(self):
        self._clear_grid()
        self.count_label.setText(f"{len(self.anime_list)} title{'s' if len(self.anime_list) != 1 else ''}")
        if not self.anime_list:
            empty = QLabel("Nothing here yet\n\nAdd titles from Search to build your collection.")
            empty.setAlignment(Qt.AlignCenter); empty.setStyleSheet(f"color:{COLORS['muted']};font-size:15px;padding:100px;")
            self.grid_layout.addWidget(empty, 0, 0, 1, 4); return

        columns = self._column_count()
        for i, anime in enumerate(self.anime_list):
            card = WorkCard(anime, mode="library")
            card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            card.clicked.connect(self.work_selected)
            self.grid_layout.addWidget(card, i // columns, i % columns, Qt.AlignTop | Qt.AlignLeft)

    def _reflow_grid(self):
        self._populate()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start()
