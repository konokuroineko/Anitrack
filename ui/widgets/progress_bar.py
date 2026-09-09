from PySide6.QtWidgets import QProgressBar

from ui.theme import COLORS


class ProgressBar(QProgressBar):

    def __init__(self, value=0, maximum=0, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(6)
        self.setRange(0, maximum if maximum > 0 else 1)
        self.setValue(min(value, self.maximum()))
        self.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['border']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
