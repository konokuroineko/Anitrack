COLORS = {
    "background": "#0b0d0f",
    "background_alt": "#101317",
    "sidebar": "#0e1012",
    "surface": "#14181c",
    "surface_alt": "#181d22",
    "surface_hover": "#1d2329",
    "border": "#252c33",
    "border_hover": "#36414b",
    "primary": "#f3f5f7",
    "secondary": "#b2bbc4",
    "muted": "#747f89",
    "accent": "#e7a15b",
    "accent_hover": "#f0b46f",
    "accent_soft": "#332416",
    "success": "#74c58a",
    "danger": "#e27878",
}

FONT_SIZES = {"tiny": 10, "small": 11, "body": 13, "subtitle": 12, "large": 16, "heading": 22, "page_title": 30}
SPACING = {"xs": 4, "sm": 8, "md": 14, "lg": 20, "xl": 28, "xxl": 40}


def application_stylesheet():
    return f"""
        QMainWindow, QWidget {{ background: {COLORS['background']}; color: {COLORS['primary']}; font-family: "Segoe UI"; font-size: 13px; }}
        QToolTip {{ background: {COLORS['surface_alt']}; color: {COLORS['primary']}; border: 1px solid {COLORS['border']}; padding: 7px 9px; }}
        QLineEdit, QComboBox, QSpinBox {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 10px; color: {COLORS['primary']}; padding: 10px 12px; selection-background-color: {COLORS['accent']}; }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {COLORS['accent']}; }}
        QPushButton {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: 9px; color: {COLORS['secondary']}; padding: 9px 13px; font-weight: 600; }}
        QPushButton:hover {{ background: {COLORS['surface_hover']}; border-color: {COLORS['border_hover']}; color: {COLORS['primary']}; }}
        QPushButton:pressed {{ background: {COLORS['surface_alt']}; }}
        QPushButton:disabled {{ color: {COLORS['muted']}; background: {COLORS['background_alt']}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px 0; }}
        QScrollBar::handle:vertical {{ background: {COLORS['border']}; border-radius: 4px; min-height: 36px; }}
        QScrollBar::handle:vertical:hover {{ background: {COLORS['muted']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ background: transparent; height: 9px; }}
        QScrollBar::handle:horizontal {{ background: {COLORS['border']}; border-radius: 4px; min-width: 36px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """


def panel_stylesheet(radius=14):
    return f"QFrame {{ background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: {radius}px; }}"


def muted_label_stylesheet():
    return f"color: {COLORS['muted']}; font-size: 12px;"
