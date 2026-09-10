from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from database import get_all_library
from ui.theme import COLORS, SPACING, muted_label_stylesheet


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["lg"])

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 30px; font-weight: 750; color: {COLORS['primary']};")
        layout.addWidget(title)

        subtitle = QLabel("Local application settings and data information")
        subtitle.setStyleSheet(muted_label_stylesheet())
        layout.addWidget(subtitle)

        info = QFrame()
        info.setStyleSheet(f"QFrame {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 12px; }}")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])

        library_count = len(list(get_all_library()))
        for heading, value in [
            ("Library titles", str(library_count)),
            ("Database", "Local SQLite database"),
            ("Covers", "Cached locally when available"),
            ("AniList", "Used for online metadata and search"),
        ]:
            row = QLabel(f"{heading}\n{value}")
            row.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row.setStyleSheet(f"color: {COLORS['secondary']}; padding: 8px 0; border: none;")
            info_layout.addWidget(row)

        layout.addWidget(info)
        layout.addStretch()
