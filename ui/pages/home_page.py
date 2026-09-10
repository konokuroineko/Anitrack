from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from database import get_all_library
from ui.theme import COLORS, SPACING


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

        old.setContentsMargins(SPACING["xxl"], SPACING["xxl"], SPACING["xxl"], SPACING["xxl"])
        old.setSpacing(SPACING["lg"])

        library = list(get_all_library())
        watching = sum(1 for item in library if item["status"] == "Watching")
        completed = sum(1 for item in library if item["status"] == "Completed")
        planned = sum(1 for item in library if item["status"] == "Planning")

        heading = QLabel("Overview")
        heading.setStyleSheet(f"font-size: 28px; font-weight: 750; color: {COLORS['primary']};")
        old.addWidget(heading)

        rule = QFrame()
        rule.setFixedHeight(1)
        rule.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        old.addWidget(rule)
        old.addSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(SPACING["md"])
        cards = [
            (len(library), "All", "Everything in your library", COLORS["accent"]),
            (watching, "Watching", "Currently in progress", COLORS["success"]),
            (completed, "Completed", "Finished titles", COLORS["primary"]),
            (planned, "Planned", "Saved for later", COLORS["secondary"]),
        ]
        for value, label, hint, accent in cards:
            card = QFrame()
            card.setObjectName("statCard")
            card.setMinimumHeight(160)
            card.setStyleSheet(f"""
                QFrame#statCard {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 16px; }}
                QFrame#statCard:hover {{ background: {COLORS['surface_hover']}; border-color: {COLORS['border_hover']}; }}
            """)
            box = QVBoxLayout(card)
            box.setContentsMargins(22, 20, 22, 20)
            number = QLabel(str(value))
            number.setStyleSheet(f"font-size: 42px; font-weight: 800; color: {accent}; border: none; background: transparent;")
            name = QLabel(label)
            name.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLORS['primary']}; border: none; background: transparent;")
            hint_label = QLabel(hint)
            hint_label.setStyleSheet(f"font-size: 11px; color: {COLORS['muted']}; border: none; background: transparent;")
            box.addWidget(number)
            box.addWidget(name)
            box.addStretch()
            box.addWidget(hint_label)
            row.addWidget(card, 1)

        old.addLayout(row)
        old.addStretch()
