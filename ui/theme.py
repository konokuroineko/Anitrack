COLORS = {
    "background": "#0a0b0e",
    "background_alt": "#0f1116",
    "sidebar": "#0b0d11",
    "surface": "#13161c",
    "surface_alt": "#191d25",
    "surface_hover": "#202631",
    "border": "#252b35",
    "border_hover": "#394250",
    "primary": "#f5f7fa",
    "secondary": "#aeb7c4",
    "muted": "#687384",
    "accent": "#ff9f43",
    "accent_hover": "#ffb765",
    "accent_soft": "#302116",
    "success": "#67d391",
    "danger": "#ef7474",
    "panel": "#11141a",
    "panel_soft": "#171b22",
    "card": "#12151b",
    "card_hover": "#1a1f27",
}

FONT_SIZES = {"tiny": 10, "small": 11, "body": 13, "subtitle": 12, "large": 16, "heading": 24, "page_title": 32}
SPACING = {"xs": 4, "sm": 8, "md": 14, "lg": 20, "xl": 28, "xxl": 40}


def application_stylesheet():
    return f"""
        * {{ outline: none; }}
        QMainWindow, QWidget {{ background: {COLORS['background']}; color: {COLORS['primary']}; font-family: "Segoe UI"; font-size: 13px; }}
        QLabel, QCheckBox, QRadioButton {{ background: transparent; }}
        QToolTip {{ background: {COLORS['surface_alt']}; color: {COLORS['primary']}; border: 1px solid {COLORS['border']}; padding: 7px 9px; }}
        QLineEdit, QComboBox, QSpinBox {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 10px; color: {COLORS['primary']}; padding: 10px 12px; selection-background-color: {COLORS['accent']}; }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {COLORS['accent']}; }}
        QPushButton {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 9px; color: {COLORS['secondary']}; padding: 9px 13px; font-weight: 600; }}
        QPushButton:hover {{ background: {COLORS['surface_hover']}; border-color: {COLORS['border_hover']}; color: {COLORS['primary']}; }}
        QPushButton:pressed {{ background: {COLORS['surface_alt']}; }}
        QPushButton:disabled {{ color: {COLORS['muted']}; background: {COLORS['background_alt']}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px 0; }}
        QScrollBar::handle:vertical {{ background: {COLORS['border']}; border-radius: 4px; min-height: 36px; }}
        QScrollBar::handle:vertical:hover {{ background: {COLORS['muted']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ background: transparent; height: 8px; }}
        QScrollBar::handle:horizontal {{ background: {COLORS['border']}; border-radius: 4px; min-width: 36px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """


def panel_stylesheet(radius=16):
    return f"QFrame {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: {radius}px; }}"


def card_stylesheet(radius=12):
    return f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: {radius}px; }} QFrame:hover {{ background: {COLORS['card_hover']}; border-color: {COLORS['border_hover']}; }}"


def muted_label_stylesheet():
    return f"color: {COLORS['muted']}; font-size: 12px;"
