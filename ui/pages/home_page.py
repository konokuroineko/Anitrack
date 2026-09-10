from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

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

        library = list(get_all_library())
        watching = [x for x in library if x["status"] == "Watching"]
        completed = [x for x in library if x["status"] == "Completed"]
        planned = [x for x in library if x["status"] == "Planning"]

        stats = QHBoxLayout()
        stats.setSpacing(SPACING["md"])
        for value, label in [
            (len(library), "All"),
            (len(watching), "Watching"),
            (len(completed), "Completed"),
            (len(planned), "Planned"),
        ]:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {COLORS['panel']}; "
                f"border: 1px solid {COLORS['border']}; border-radius: 12px; }}"
            )
            layout = QVBoxLayout(card)
            layout.setContentsMargins(
                SPACING["lg"], SPACING["md"], SPACING["lg"], SPACING["md"]
            )
            number = QLabel(str(value))
            number.setStyleSheet(
                f"font-size: 28px; font-weight: 750; color: {COLORS['primary']}; border: none;"
            )
            name = QLabel(label)
            name.setStyleSheet(muted_label_stylesheet())
            layout.addWidget(number)
            layout.addWidget(name)
            stats.addWidget(card)

        old.addLayout(stats)
        old.addStretch()
