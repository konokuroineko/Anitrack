import threading

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from database import add_to_library, get_work, initialize_database, save_anime, save_characters, save_cover_path, save_episodes, save_staff
from image_cache import download_cover
from ui.navigation import NavigationController
from ui.theme import COLORS, application_stylesheet
from ui.pages.character_page import CharacterPage
from ui.pages.home_page import HomePage
from ui.pages.library_page import LibraryPage
from ui.pages.person_page import PersonPage
from ui.pages.relationship_page import RelationshipPage
from ui.pages.search_page import SearchPage
from ui.pages.settings_page import SettingsPage
from ui.pages.work_detail_page import WorkDetailPage


class ImageWorker(QObject):
    finished = Signal(int, object)
    error = Signal(int, str)

    def __init__(self, work_id, image_url):
        super().__init__()
        self.work_id = work_id
        self.image_url = image_url

    def run(self):
        try:
            self.finished.emit(self.work_id, download_cover(self.work_id, self.image_url))
        except Exception as error:
            self.error.emit(self.work_id, str(error))


class NavigationButton(QPushButton):
    def __init__(self, icon_text, label):
        super().__init__(f"{icon_text}   {label}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setProperty("navButton", True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        initialize_database()
        self.setWindowTitle("Anitrack")
        self.resize(1320, 820)
        self.image_threads = []
        self.navigation_buttons = {}
        self.setup_ui()

    def setup_ui(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 20, 18, 18)
        side.setSpacing(5)

        logo = QLabel("ANITRACK")
        logo.setStyleSheet(f"color: {COLORS['primary']}; font-size: 20px; font-weight: 800; letter-spacing: 2px; padding: 8px 10px 0;")
        side.addWidget(logo)
        sub = QLabel("Your personal media library")
        sub.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; padding: 0 10px;")
        side.addWidget(sub)
        side.addSpacing(24)

        self.stack = QStackedWidget()
        self.navigation = NavigationController(self.stack)

        self.library_page = LibraryPage()
        self.search_page = SearchPage(self.add_to_library)
        self.work_detail_page = WorkDetailPage()
        pages = {
            "home": HomePage(),
            "collections": self.library_page,
            "search": self.search_page,
            "work_detail": self.work_detail_page,
            "person": PersonPage(),
            "character": CharacterPage(),
            "relationships": RelationshipPage(),
            "settings": SettingsPage(),
        }
        for name, page in pages.items():
            self.navigation.add_page(name, page)

        for title, items in [
            ("LIBRARY", [("⌂", "Home", "home"), ("▦", "Library", "collections"), ("⌕", "Search", "search")]),
            ("EXPLORE", [("♙", "People", "person"), ("♧", "Characters", "character"), ("◇", "Relations", "relationships")]),
        ]:
            label = QLabel(title)
            label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 10px; font-weight: 800; letter-spacing: 1.4px; padding: 8px 10px 4px;")
            side.addWidget(label)
            for icon, text, page_name in items:
                self._add_nav(side, icon, text, page_name)
            side.addSpacing(8)

        side.addStretch()
        self._add_nav(side, "⚙", "Settings", "settings")

        self.navigation.page_changed.connect(self.update_navigation_state)
        self.library_page.work_selected.connect(self.show_work_details)
        self.search_page.anime_selected.connect(self.show_search_work)
        self.work_detail_page.back_requested.connect(lambda: self.navigation.show("collections"))
        self.work_detail_page.relation_selected.connect(self.show_relation)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(application_stylesheet() + f"""
            QFrame#sidebar {{ background: {COLORS['sidebar']}; border-right: 1px solid {COLORS['border']}; }}
            QPushButton[navButton="true"] {{ background: transparent; border: 1px solid transparent; color: {COLORS['secondary']}; border-radius: 10px; padding: 10px 12px; text-align: left; font-size: 13px; font-weight: 600; }}
            QPushButton[navButton="true"]:hover {{ background: {COLORS['surface']}; color: {COLORS['primary']}; }}
            QPushButton[navButton="true"]:checked {{ background: {COLORS['accent_soft']}; border-color: #5d432c; color: {COLORS['accent_hover']}; }}
        """)
        self.navigation.show("home")

    def _add_nav(self, layout, icon, label, page_name):
        button = NavigationButton(icon, label)
        self.navigation_buttons[page_name] = button
        button.clicked.connect(lambda checked=False, name=page_name: self.navigation.show(name))
        layout.addWidget(button)

    def update_navigation_state(self, page_name):
        for name, button in self.navigation_buttons.items():
            button.setChecked(name == page_name)

    def show_work_details(self, work):
        self.work_detail_page.set_work(work)
        self.navigation.show("work_detail")

    def show_search_work(self, work):
        try:
            from api import get_media_details
            details = get_media_details(work["id"])
            save_anime(details)
            save_characters(work["id"], (details.get("characters") or {}).get("edges"))
            save_staff(work["id"], (details.get("staff") or {}).get("edges"))
            save_episodes(work["id"], details.get("streamingEpisodes"))
            stored = get_work(work["id"])
            self.show_work_details(stored or work)
        except Exception:
            self.show_work_details(work)

    def show_relation(self, relation):
        work_id = relation.get("target_id") if relation else None
        work = get_work(work_id) if work_id else None
        if work:
            self.show_work_details(work)

    def add_to_library(self, anime, button):
        try:
            save_anime(anime)
            save_characters(anime["id"], (anime.get("characters") or {}).get("edges"))
            save_episodes(anime["id"], anime.get("streamingEpisodes"))
            save_staff(anime["id"], (anime.get("staff") or {}).get("edges"))
            add_to_library(anime["id"], "Planning")
            button.setText("Added")
            button.setEnabled(False)
            self.start_cover_download(anime["id"], (anime.get("coverImage") or {}).get("large"), button)
        except Exception as error:
            button.setText("Error")
            self.search_page.results_title.setText(f"Could not save: {error}")

    def start_cover_download(self, work_id, image_url, button):
        if not image_url:
            return
        worker = ImageWorker(work_id, image_url)
        worker.finished.connect(self.cover_download_finished)
        worker.error.connect(self.cover_download_error)
        thread = threading.Thread(target=worker.run, daemon=True)
        self.image_threads.append(thread)
        thread.start()
        button.setProperty("cover_work_id", work_id)

    def cover_download_finished(self, work_id, cover_path):
        if cover_path:
            save_cover_path(work_id, cover_path)
        self._finish_cover_button(work_id)

    def cover_download_error(self, work_id, message):
        self._finish_cover_button(work_id, f"Cover unavailable: {message}")

    def _finish_cover_button(self, work_id, tooltip=None):
        for button in self.findChildren(QPushButton):
            if button.property("cover_work_id") == work_id:
                button.setText("Added")
                if tooltip:
                    button.setToolTip(tooltip)
                break
