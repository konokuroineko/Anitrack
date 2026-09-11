from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget, QLayout

from database import get_all_library
from ui.theme import COLORS
from ui.widgets.work_card import WorkCard


class FlowLayout(QLayout):
    """Fixed-width flowing layout that lets Qt handle resize geometry naturally."""

    def __init__(self, parent=None, margin=0, h_spacing=24, v_spacing=30):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        margins = self.contentsMargins()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        effective = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            widget_size = item.sizeHint()
            if widget_size.width() <= 0:
                continue

            next_x = x + widget_size.width()
            if x > effective.x() and next_x > effective.right() + 1:
                x = effective.x()
                y += line_height + self._v_spacing
                next_x = x + widget_size.width()
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), widget_size))

            x = next_x + self._h_spacing
            line_height = max(line_height, widget_size.height())

        return y + line_height - rect.y() + margins.bottom()


class LibraryPage(QWidget):
    work_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.all_anime = []
        self.anime_list = []
        self.current_filter = "All"
        self.current_sort = "Recently Added"
        self._cards = []
        self._empty_label = None
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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.flow_layout = FlowLayout(container, h_spacing=24, v_spacing=30)
        self.scroll_area.setWidget(container)
        root.addWidget(self.scroll_area, 1)
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
        self.current_sort = value; self._populate()

    def _clear_cards(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._cards = []
        self._empty_label = None

    def _populate(self):
        self._clear_cards()
        self.count_label.setText(f"{len(self.anime_list)} title{'s' if len(self.anime_list) != 1 else ''}")
        if not self.anime_list:
            empty = QLabel("Nothing here yet\n\nAdd titles from Search to build your collection.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color:{COLORS['muted']};font-size:15px;padding:100px;")
            self.flow_layout.addWidget(empty)
            self._empty_label = empty
            return

        for anime in self.anime_list:
            card = WorkCard(anime, mode="library")
            card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            card.clicked.connect(self.work_selected)
            self._cards.append(card)
            self.flow_layout.addWidget(card)
