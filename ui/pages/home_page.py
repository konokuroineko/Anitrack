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

        section = QLabel("My Library")
        section.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['primary']};")
        old.addWidget(section)

        for label, items in [
            ("Watching", watching),
            ("Completed", completed),
            ("Planned", planned),
        ]:
            header = QHBoxLayout()
            heading = QLabel(label)
            heading.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['primary']};")
            count = QLabel(str(len(items)))
            count.setStyleSheet(muted_label_stylesheet())
            header.addWidget(heading)
            header.addWidget(count)
            header.addStretch()
            old.addLayout(header)

            if items:
                row = QHBoxLayout()
                row.setSpacing(SPACING["md"])
                for anime in items[:5]:
                    card = QFrame()
                    card.setStyleSheet(f"QFrame {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}")
                    card_layout = QVBoxLayout(card)
                    card_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
                    title = QLabel(anime["title"] or "Untitled")
                    title.setWordWrap(True)
                    title.setStyleSheet(f"font-weight: 650; color: {COLORS['primary']}; border: none;")
                    card_layout.addWidget(title)
                    if label == "Watching":
                        progress = anime["progress_episodes"] or 0
                        total = anime["episodes"] or 0
                        progress_text = QLabel(
                            f"Episode {progress} / {total}" if total else f"Episode {progress}"
                        )
                        progress_text.setStyleSheet(f"color: {COLORS['muted']}; border: none;")
                        card_layout.addWidget(progress_text)
                    else:
                        media_type = anime["type"] or "Media"
                        meta = QLabel(media_type)
                        meta.setStyleSheet(f"color: {COLORS['muted']}; border: none;")
                        card_layout.addWidget(meta)
                    row.addWidget(card, 1)
                for _ in range(5 - min(5, len(items))):
                    row.addStretch(1)
                old.addLayout(row)
            else:
                empty = QLabel(f"No {label.lower()} titles yet.")
                empty.setStyleSheet(muted_label_stylesheet())
                old.addWidget(empty)

        old.addStretch()
