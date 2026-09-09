import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
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

from database import get_characters, get_episodes, get_relations, get_staff
from ui.theme import COLORS, SPACING, muted_label_stylesheet
from ui.widgets.character_card import CharacterCard
from ui.widgets.info_section import InfoSection
from ui.widgets.person_card import PersonCard
from ui.widgets.relation_card import RelationCard
from ui.widgets.section_header import SectionHeader
from ui.widgets.progress_bar import ProgressBar


class WorkDetailPage(QWidget):
    back_requested = Signal()
    person_selected = Signal(object)
    character_selected = Signal(object)
    relation_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.work = None
        self.content_layout = None
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

    def set_work(self, work):
        self.work = work
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'],
            SPACING['lg'], SPACING['lg']
        )
        self.content_layout.setSpacing(SPACING['md'])
        self.scroll_area.setWidget(content)

        back_button = QPushButton("Back to Collections")
        back_button.clicked.connect(self.back_requested)
        self.content_layout.addWidget(back_button, alignment=Qt.AlignLeft)
        self.content_layout.addWidget(self._build_hero())
        self.content_layout.addWidget(self._build_description())
        self.content_layout.addWidget(self._build_characters())
        self.content_layout.addWidget(self._build_staff())
        self.content_layout.addWidget(self._build_relations())
        self.content_layout.addWidget(self._build_music())
        self.content_layout.addStretch()

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
        layout.setContentsMargins(
            SPACING['xl'], SPACING['xl'],
            SPACING['xl'], SPACING['xl']
        )
        layout.setSpacing(SPACING['xl'])

        cover = QLabel()
        cover.setFixedSize(250, 350)
        cover.setAlignment(Qt.AlignCenter)
        cover_path = self.work['cover_path']
        if cover_path:
            pixmap = QPixmap(cover_path)
            if not pixmap.isNull():
                cover.setPixmap(pixmap.scaled(
                    cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
        layout.addWidget(cover, alignment=Qt.AlignTop)

        details = QVBoxLayout()
        title = QLabel(self.work['title'])
        title.setStyleSheet(
            f"color: {COLORS['primary']}; font-size: 32px; font-weight: 700;"
        )
        title.setWordWrap(True)
        details.addWidget(title)

        metadata = " • ".join(
            str(value) for value in [
                self.work['format'],
                self.work['start_year'],
                f"{self.work['episodes']} Episodes" if self.work['episodes'] else None,
            ] if value
        )
        metadata_label = QLabel(metadata or "Media details unavailable")
        metadata_label.setStyleSheet(muted_label_stylesheet())
        details.addWidget(metadata_label)

        score = self.work['score']
        score_label = QLabel(f"★ {score}%" if score else "No score")
        score_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 18px; font-weight: 600;"
        )
        details.addWidget(score_label)

        progress = self.work['progress_episodes'] or 0
        total = self.work['episodes'] or 0
        progress_label = QLabel(
            f"Episode {progress} / {total}" if total else f"Episode {progress}"
        )
        progress_label.setStyleSheet(muted_label_stylesheet())
        details.addSpacing(SPACING['md'])
        details.addWidget(progress_label)
        details.addWidget(ProgressBar(progress, total))
        details.addStretch()
        layout.addLayout(details, 1)
        return hero

    def _build_description(self):
        section = InfoSection("Description")
        description = QLabel(self.work['description'] or "No description saved.")
        description.setWordWrap(True)
        description.setTextFormat(Qt.PlainText)
        description.setStyleSheet(
            f"color: {COLORS['secondary']}; font-size: 14px; line-height: 1.4;"
        )
        section.add_widget(description)
        return section

    def _build_characters(self):
        section = InfoSection("Characters")
        characters = get_characters(self.work['id'])
        if not characters:
            section.add_message("No character data imported yet.")
            return section
        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING['md'])
        grid.setVerticalSpacing(SPACING['md'])
        for index, character in enumerate(characters):
            card = CharacterCard(character)
            card.clicked.connect(self.character_selected)
            grid.addWidget(card, index // 3, index % 3)
        section.add_widget(self._grid_widget(grid))
        return section

    def _build_staff(self):
        section = InfoSection("Staff")
        staff = get_staff(self.work['id'])
        if not staff:
            section.add_message("No staff data imported yet.")
            return section
        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING['md'])
        grid.setVerticalSpacing(SPACING['md'])
        for index, member in enumerate(staff):
            card = PersonCard(member)
            card.clicked.connect(self.person_selected)
            grid.addWidget(card, index // 4, index % 4)
        section.add_widget(self._grid_widget(grid))
        return section

    def _build_relations(self):
        section = InfoSection("Relations")
        relations = get_relations(self.work['id'])
        if not relations:
            section.add_message("No related works imported yet.")
            return section
        grid = QGridLayout()
        grid.setHorizontalSpacing(SPACING['md'])
        grid.setVerticalSpacing(SPACING['md'])
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

    def _grid_widget(self, grid):
        widget = QWidget()
        widget.setLayout(grid)
        return widget
