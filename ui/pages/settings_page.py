from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from database import get_all_library
from ui.theme import COLORS, SPACING


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["xxl"], SPACING["xxl"], SPACING["xxl"], SPACING["xxl"])
        layout.setSpacing(SPACING["lg"])

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {COLORS['primary']};")
        layout.addWidget(title)
        subtitle = QLabel("Application and local data")
        subtitle.setStyleSheet(f"color: {COLORS['muted']};")
        layout.addWidget(subtitle)

        panel = QFrame()
        panel.setStyleSheet(f"QFrame {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 16px; }}")
        box = QVBoxLayout(panel)
        box.setContentsMargins(24, 20, 24, 20)
        box.setSpacing(0)
        library_count = len(list(get_all_library()))
        rows = [
            ("Library", f"{library_count} saved titles"),
            ("Storage", "Local SQLite database"),
            ("Artwork", "Cached locally when downloaded"),
            ("Metadata", "AniList powers online search and detail import"),
        ]
        for name, value in rows:
            row = QLabel(f"{name}\n{value}")
            row.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row.setStyleSheet(f"color: {COLORS['secondary']}; padding: 14px 0; border-bottom: 1px solid {COLORS['border']};")
            box.addWidget(row)
        layout.addWidget(panel)
        layout.addStretch()
