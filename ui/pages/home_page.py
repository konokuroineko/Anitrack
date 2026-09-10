from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from database import get_all_library
from ui.theme import COLORS, SPACING, muted_label_stylesheet


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.refresh()

    def refresh(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        else:
            old = QVBoxLayout(self)

        old.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        old.setSpacing(SPACING["lg"])

        greeting = QLabel("Welcome back")
        greeting.setStyleSheet(f"font-size: 34px; font-weight: 750; color: {COLORS['primary']};")
        old.addWidget(greeting)

        subtitle = QLabel("Your anime, manga, and reading library — all in one place.")
        subtitle.setStyleSheet(muted_label_stylesheet())
        old.addWidget(subtitle)

        library = list(get_all_library())
        watching = [x for x in library if x["status"] == "Watching"]
        completed = [x for x in library if x["status"] == "Completed"]
        planned = [x for x in library if x["status"] == "Planning"]

        stats = QHBoxLayout()
        stats.setSpacing(SPACING["md"])
        for value, label in [
            (len(library), "Library"),
            (len(watching), "Watching"),
            (len(completed), "Completed"),
            (len(planned), "Planned"),
        ]:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 12px; }}")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"])
            number = QLabel(str(value))
            number.setStyleSheet(f"font-size: 28px; font-weight: 750; color: {COLORS['primary']}; border: none;")
            name = QLabel(label)
            name.setStyleSheet(f"color: {COLORS['muted']}; border: none;")
            layout.addWidget(number)
            layout.addWidget(name)
            stats.addWidget(card)
        old.addLayout(stats)

        section = QLabel("Continue watching")
        section.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['primary']};")
        old.addWidget(section)

        if watching:
            for anime in watching[:5]:
                row = QFrame()
                row.setStyleSheet(f"QFrame {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
                title = QLabel(anime["title"] or "Untitled")
                title.setStyleSheet(f"font-weight: 650; color: {COLORS['primary']}; border: none;")
                progress = anime["progress_episodes"] or 0
                total = anime["episodes"] or 0
                progress_text = QLabel(f"Episode {progress} / {total}" if total else f"Episode {progress}")
                progress_text.setStyleSheet(f"color: {COLORS['muted']}; border: none;")
                row_layout.addWidget(title)
                row_layout.addStretch()
                row_layout.addWidget(progress_text)
                old.addWidget(row)
        else:
            empty = QLabel("Nothing here yet. Add something to your library from Search.")
            empty.setStyleSheet(muted_label_stylesheet())
            old.addWidget(empty)

        old.addStretch()
