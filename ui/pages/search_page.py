from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from api import search_anime
from ui.theme import COLORS, SPACING, muted_label_stylesheet
from ui.widgets.section_header import SectionHeader
from ui.widgets.work_card import WorkCard


class InfiniteScrollArea(QScrollArea):
    scroll_to_bottom = Signal()

    def __init__(self):
        super().__init__()
        self.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

    def check_scroll_position(self):
        scrollbar = self.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - 100:
            self.scroll_to_bottom.emit()


class SearchWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, search_text, page=1):
        super().__init__()
        self.search_text = search_text
        self.page = page

    def run(self):
        try:
            self.finished.emit(search_anime(self.search_text, self.page))
        except Exception as error:
            self.error.emit(str(error))


class SearchPage(QWidget):
    anime_selected = Signal(object)

    def __init__(self, add_to_library):
        super().__init__()
        self.add_to_library = add_to_library
        self.current_search = ""
        self.current_page = 1
        self.has_next_page = False
        self.is_loading = False
        self.threads = []
        self.workers = []
        self.grid_container = None
        self.grid_layout = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        layout.addWidget(SectionHeader("Search"))

        search_layout = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search anime...")
        self.search_button = QPushButton("Search")
        search_layout.addWidget(self.search, 1)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        filters = QHBoxLayout()
        self.media_filter = QComboBox()
        self.media_filter.addItems(["Anime", "Manga", "Novels"])
        self.media_filter.setToolTip("Media type filter; anime is currently supported")
        filters.addWidget(self.media_filter)
        filters.addStretch()
        layout.addLayout(filters)

        title_layout = QHBoxLayout()
        self.results_title = QLabel("Results")
        self.results_title.setObjectName("heading")
        title_layout.addWidget(self.results_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        self.results_scroll = InfiniteScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(SPACING["md"])
        self.grid_layout.setVerticalSpacing(SPACING["md"])
        self.results_scroll.setWidget(self.grid_container)
        self.results_scroll.scroll_to_bottom.connect(self.load_more_results)
        layout.addWidget(self.results_scroll, 1)

        self.search_button.clicked.connect(self.search_clicked)
        self.search.returnPressed.connect(self.search_clicked)

    def search_clicked(self):
        search_text = self.search.text().strip()
        if not search_text:
            return
        self.current_search = search_text
        self.current_page = 1
        self.has_next_page = False
        self.is_loading = True
        self.clear_results()
        self.show_message("Searching AniList...", muted=True)
        self.search_button.setEnabled(False)
        self.start_search(search_text, 1)

    def load_more_results(self):
        if not self.current_search or not self.has_next_page or self.is_loading:
            return
        self.is_loading = True
        self.start_search(self.current_search, self.current_page + 1)

    def start_search(self, search_text, page):
        thread = QThread()
        worker = SearchWorker(search_text, page)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self.search_finished)
        worker.error.connect(self.search_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
        thread.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.threads.append(thread)
        self.workers.append(worker)
        thread.start()

    def search_finished(self, page_data):
        self.search_button.setEnabled(True)
        self.is_loading = False
        self.current_page = page_data["pageInfo"]["currentPage"]
        self.has_next_page = page_data["pageInfo"]["hasNextPage"]
        if self.current_page == 1:
            self.clear_results()
        results = page_data["media"]
        if not results and self.current_page == 1:
            self.show_message("No results found.\nTry another search.")
            return
        for anime in results:
            card = WorkCard(
                anime,
                mode="search",
                add_callback=self.add_to_library
            )
            card.clicked.connect(self.anime_selected)
            self.grid_layout.addWidget(card)

    def search_error(self, message):
        self.search_button.setEnabled(True)
        self.is_loading = False
        self.clear_results()
        self.show_message("Could not reach AniList.\nTry again.", error=True)
        retry_button = QPushButton("Retry")
        retry_button.clicked.connect(self.search_clicked)
        self.grid_layout.addWidget(retry_button)

    def show_message(self, message, muted=False, error=False):
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        if muted:
            label.setStyleSheet(muted_label_stylesheet())
        elif error:
            label.setStyleSheet(f"color: {COLORS['danger']};")
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
        if not self.grid_layout:
            return
        cards = [
            self.grid_layout.itemAt(index).widget()
            for index in range(self.grid_layout.count())
            if self.grid_layout.itemAt(index).widget()
            and isinstance(self.grid_layout.itemAt(index).widget(), WorkCard)
        ]
        for card in cards:
            self.grid_layout.removeWidget(card)
        columns = max(1, self.results_scroll.viewport().width() // 196)
        for index, card in enumerate(cards):
            self.grid_layout.addWidget(card, index // columns, index % columns)

    def closeEvent(self, event):
        for thread in self.threads[:]:
            if thread.isRunning():
                thread.quit()
                if not thread.wait(2000):
                    thread.terminate()
                    thread.wait()
        event.accept()
