from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from api import search_anime
from ui.theme import COLORS, SPACING
from ui.widgets.work_card import WorkCard


class InfiniteScrollArea(QScrollArea):
    scroll_to_bottom = Signal()
    def __init__(self):
        super().__init__()
        self.verticalScrollBar().valueChanged.connect(self._check)
    def _check(self):
        bar = self.verticalScrollBar()
        if bar.value() >= bar.maximum() - 120:
            self.scroll_to_bottom.emit()


class SearchWorker(QObject):
    finished = Signal(object)
    error = Signal(str)
    def __init__(self, search_text, page, media_type):
        super().__init__()
        self.search_text, self.page, self.media_type = search_text, page, media_type
    def run(self):
        try:
            self.finished.emit(search_anime(self.search_text, self.page, media_type=self.media_type))
        except Exception as error:
            self.error.emit(str(error))


class SearchPage(QWidget):
    anime_selected = Signal(object)
    def __init__(self, add_to_library):
        super().__init__()
        self.add_to_library = add_to_library
        self.current_search = ""
        self.current_media_type = "ANIME"
        self.current_page = 1
        self.has_next_page = False
        self.is_loading = False
        self.threads, self.workers = [], []
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING["xxl"], SPACING["xxl"], SPACING["xxl"], SPACING["xxl"])
        root.setSpacing(SPACING["lg"])

        heading = QLabel("Search")
        heading.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {COLORS['primary']};")
        root.addWidget(heading)

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search anime, manga, or novels")
        self.search.setMinimumHeight(44)
        self.search_button = QPushButton("Search")
        self.search_button.setMinimumHeight(44)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.search_button)
        root.addLayout(bar)

        filter_row = QHBoxLayout()
        self.media_filter = QComboBox()
        self.media_filter.addItems(["Anime", "Manga", "Novels"])
        self.media_filter.setFixedWidth(150)
        filter_row.addWidget(self.media_filter)
        self.results_title = QLabel("Discover something new")
        self.results_title.setStyleSheet(f"color: {COLORS['muted']}; font-size: 12px;")
        filter_row.addSpacing(8)
        filter_row.addWidget(self.results_title)
        filter_row.addStretch()
        root.addLayout(filter_row)

        self.results_scroll = InfiniteScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 4, 0, 4)
        self.grid_layout.setHorizontalSpacing(SPACING["lg"])
        self.grid_layout.setVerticalSpacing(SPACING["xl"])
        self.results_scroll.setWidget(self.grid_container)
        self.results_scroll.scroll_to_bottom.connect(self.load_more_results)
        root.addWidget(self.results_scroll, 1)

        self.search_button.clicked.connect(self.search_clicked)
        self.search.returnPressed.connect(self.search_clicked)
        self.media_filter.currentIndexChanged.connect(self.media_filter_changed)

    def media_filter_changed(self):
        if self.current_search:
            self.search_clicked()

    def selected_media_type(self):
        return {"Anime": "ANIME", "Manga": "MANGA", "Novels": "MANGA"}[self.media_filter.currentText()]

    def search_clicked(self):
        text = self.search.text().strip()
        if not text or self.is_loading:
            return
        self.current_search = text
        self.current_media_type = self.selected_media_type()
        self.current_page = 1
        self.has_next_page = False
        self.clear_results()
        self.results_title.setText(f"Searching for “{text}”")
        self.search_button.setEnabled(False)
        self.is_loading = True
        self.start_search(text, 1)

    def load_more_results(self):
        if self.current_search and self.has_next_page and not self.is_loading:
            self.is_loading = True
            self.start_search(self.current_search, self.current_page + 1)

    def start_search(self, text, page):
        thread = QThread()
        worker = SearchWorker(text, page, self.current_media_type)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self.search_finished)
        worker.error.connect(self.search_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.threads.append(thread)
        self.workers.append(worker)
        thread.start()

    def search_finished(self, data):
        self.search_button.setEnabled(True)
        self.is_loading = False
        self.current_page = data["pageInfo"]["currentPage"]
        self.has_next_page = data["pageInfo"]["hasNextPage"]
        if self.current_page == 1:
            self.clear_results()
        results = data["media"]
        self.results_title.setText(f"{len(results)} results · page {self.current_page}")
        if not results and self.current_page == 1:
            self.show_message("No results found")
            return
        for anime in results:
            card = WorkCard(anime, mode="search", add_callback=self.add_to_library)
            card.clicked.connect(self.anime_selected)
            self.grid_layout.addWidget(card)
        self._reflow_cards()

    def search_error(self, message):
        self.search_button.setEnabled(True)
        self.is_loading = False
        self.clear_results()
        if "(403)" in message and "temporarily disabled" in message.lower():
            text = "AniList is temporarily unavailable.\nYour offline library still works."
        elif "(429)" in message:
            text = "AniList is rate-limiting requests.\nPlease try again shortly."
        elif "(5" in message[:20]:
            text = "AniList is having server problems.\nPlease try again later."
        else:
            text = f"Search failed.\n{message}"
        self.show_message(text)
        retry = QPushButton("Try again")
        retry.clicked.connect(self.search_clicked)
        self.grid_layout.addWidget(retry, 1, 0)

    def show_message(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 15px; padding: 60px;")
        self.grid_layout.addWidget(label, 0, 0)

    def clear_results(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_cards()

    def _reflow_cards(self):
        cards = []
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, WorkCard):
                cards.append(widget)
        for card in cards:
            self.grid_layout.removeWidget(card)
        columns = max(1, self.results_scroll.viewport().width() // 224)
        for i, card in enumerate(cards):
            self.grid_layout.addWidget(card, i // columns, i % columns)
