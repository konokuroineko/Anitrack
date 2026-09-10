from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
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

from database import (
    get_characters,
    get_episodes,
    get_relations,
    get_staff,
    set_episode_watched,
)
from ui.theme import COLORS, SPACING, muted_label_stylesheet
from ui.widgets.character_card import CharacterCard
from ui.widgets.info_section import InfoSection
from ui.widgets.person_card import PersonCard
from ui.widgets.relation_card import RelationCard
from ui.widgets.progress_bar import ProgressBar


class WorkDetailPage(QWidget):
    back_requested = Signal()
    person_selected = Signal(object)
    character_selected = Signal(object)
    relation_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.work = None
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

    def set_work(self, work):
        self.work = work
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        content_layout.setSpacing(SPACING["md"])

        back_button = QPushButton("Back to Collections")
        back_button.clicked.connect(self.back_requested)
        content_layout.addWidget(back_button, alignment=Qt.AlignLeft)
        content_layout.addWidget(self._build_hero())
        content_layout.addWidget(self._build_description())
        content_layout.addWidget(self._build_episodes())
        content_layout.addWidget(self._build_characters())
        content_layout.addWidget(self._build_staff())
        content_layout.addWidget(self._build_relations())
        content_layout.addWidget(self._build_music())
        content_layout.addStretch()
        self.scroll_area.setWidget(content)

    def _build_hero(self):
        hero = QFrame()
        hero.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["xl"])

        cover = QLabel()
        cover.setFixedSize(250, 350)
        cover.setAlignment(Qt.AlignCenter)
        cover_path = self._value("cover_path")
        if cover_path:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                cover.setPixmap(pixmap.scaled(cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            cover.setText("No cached cover")
            cover.setStyleSheet(muted_label_stylesheet())
        layout.addWidget(cover, alignment=Qt.AlignTop)

        details = QVBoxLayout()
        title = QLabel(self._value("title") or "Untitled")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-size: 32px; font-weight: 700;")
        title.setWordWrap(True)
        details.addWidget(title)

        metadata = " • ".join(str(value) for value in [
            self._value("type"),
            self._value("format"),
            self._value("start_year"),
            f"{self._value('episodes')} Episodes" if self._value("episodes") else None,
            f"{self._value('chapters')} Chapters" if self._value("chapters") else None,
        ] if value)
        metadata_label = QLabel(metadata or "Local metadata unavailable")
        metadata_label.setStyleSheet(muted_label_stylesheet())
        details.addWidget(metadata_label)

        score = self._value("score")
        score_label = QLabel(f"★ {score}%" if score else "No score saved")
        score_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 18px; font-weight: 600;")
        details.addWidget(score_label)

        progress = self._value("progress_episodes") or 0
        total = self._value("episodes") or 0
        progress_label = QLabel(f"Episode {progress} / {total}" if total else f"Episode {progress}")
        progress_label.setStyleSheet(muted_label_stylesheet())
        details.addSpacing(SPACING["md"])
        details.addWidget(progress_label)
        details.addWidget(ProgressBar(progress, total))
        details.addStretch()
        layout.addLayout(details, 1)
        return hero

    def _build_description(self):
        section = InfoSection("Description")
        description = QLabel(self._value("description") or "No description saved locally.")
        description.setWordWrap(True)
        description.setTextFormat(Qt.PlainText)
        description.setStyleSheet(f"color: {COLORS['secondary']}; font-size: 14px; line-height: 1.4;")
        section.add_widget(description)
        return section

    def _build_episodes(self):
        section = InfoSection("Episodes")
        episodes = get_episodes(self._value("id"))
        if not episodes:
            section.add_message("No episode data is stored locally for this title.")
            return section

        container = QVBoxLayout()
        container.setSpacing(SPACING["sm"])
        for episode in episodes:
            row = QFrame()
            row.setStyleSheet(f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
            row_layout = QHBoxLayout(row)
            checkbox = QCheckBox()
            checkbox.setChecked(bool(episode["watched"]))
            number = QLabel(f"Episode {episode['episode_number']}")
            number.setStyleSheet(f"color: {COLORS['primary']}; font-weight: 600;")
            row_layout.addWidget(checkbox)
            row_layout.addWidget(number)

            title = episode["title"]
            if title:
                title_label = QLabel(title)
                title_label.setWordWrap(True)
                title_label.setStyleSheet(muted_label_stylesheet())
                row_layout.addWidget(title_label, 1)
            else:
                row_layout.addStretch()

            if episode["air_date"]:
                date_label = QLabel(str(episode["air_date"]))
                date_label.setStyleSheet(muted_label_stylesheet())
                row_layout.addWidget(date_label)

            checkbox.toggled.connect(
                lambda checked, number=episode["episode_number"]: self._episode_toggled(number, checked)
            )
            container.addWidget(row)
        section.add_widget(self._layout_widget(container))
        return section

    def _episode_toggled(self, episode_number, checked):
        set_episode_watched(self._value("id"), episode_number, checked)
        # Rebuild the page so the hero progress reflects the local change.
        self.set_work(self.work)

    def _build_characters(self):
        section = InfoSection("Characters")
        characters = get_characters(self._value("id"))
        if not characters:
            section.add_message("No character data imported yet.")
            return section
        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING["md"])
        grid.setVerticalSpacing(SPACING["md"])
        for index, character in enumerate(characters):
            card = CharacterCard(character)
            card.clicked.connect(self.character_selected)
            grid.addWidget(card, index // 3, index % 3)
        section.add_widget(self._grid_widget(grid))
        return section

    def _build_staff(self):
        section = InfoSection("Staff")
        staff = get_staff(self._value("id"))
        if not staff:
            section.add_message("No staff data imported yet.")
            return section
        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING["md"])
        grid.setVerticalSpacing(SPACING["md"])
        for index, member in enumerate(staff):
            card = PersonCard(member)
            card.clicked.connect(self.person_selected)
            grid.addWidget(card, index // 4, index % 4)
        section.add_widget(self._grid_widget(grid))
        return section

    def _build_relations(self):
        section = InfoSection("Relations")
        relations = get_relations(self._value("id"))
        if not relations:
            section.add_message("No related works imported locally.")
            return section
        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING["md"])
        grid.setVerticalSpacing(SPACING["md"])
        for index, relation in enumerate(relations):
            card = RelationCard(relation)
            card.clicked.connect(self.relation_selected)
            grid.addWidget(card, index // 2, index % 2)
        section.add_widget(self._grid_widget(grid))
        return section

    def _build_music(self):
        section = InfoSection("Music")
        section.add_message("Music data is not imported yet.")
        return section

    def _value(self, key):
        if hasattr(self.work, "get"):
            return self.work.get(key)
        try:
            return self.work[key]
        except (KeyError, IndexError, TypeError):
            return None

    def _grid_widget(self, grid):
        widget = QWidget()
        widget.setLayout(grid)
        return widget

    def _layout_widget(self, layout):
        widget = QWidget()
        widget.setLayout(layout)
        return widget
