COLORS = {
    "background": "#0d0f10",
    "background_soft": "#121416",
    "sidebar": "#111315",
    "panel": "#171a1d",
    "panel_soft": "#1b1f22",
    "card": "#181c1f",
    "card_hover": "#22272b",
    "border": "#292f34",
    "border_hover": "#3a4249",

    "primary": "#f4f5f6",
    "secondary": "#b5bcc3",
    "muted": "#78818a",

    "accent": "#e4a45e",
    "accent_hover": "#efb978",
    "accent_soft": "#3a2a1c",

    "danger": "#df7474",
    "success": "#7cc58a",
}

FONT_SIZES = {
    "tiny": 10,
    "small": 11,
    "body": 13,
    "subtitle": 12,
    "large": 16,
    "heading": 22,
    "page_title": 30,
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}


def application_stylesheet():
    return f"""
        QMainWindow, QWidget {{
            background: {COLORS['background']};
            color: {COLORS['primary']};
            font-family: "Segoe UI";
            font-size: {FONT_SIZES['body']}px;
        }}

        QToolTip {{
            background: {COLORS['panel_soft']};
            color: {COLORS['primary']};
            border: 1px solid {COLORS['border']};
            padding: 6px 8px;
        }}

        QLineEdit {{
            background: {COLORS['panel']};
            border: 1px solid {COLORS['border']};
            border-radius: 9px;
            color: {COLORS['primary']};
            padding: 10px 13px;
            selection-background-color: {COLORS['accent']};
        }}

        QLineEdit:focus {{
            border-color: {COLORS['accent']};
        }}

        QComboBox, QSpinBox {{
            background: {COLORS['panel']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            color: {COLORS['primary']};
            padding: 8px 10px;
        }}

        QComboBox:hover, QSpinBox:hover {{
            border-color: {COLORS['border_hover']};
        }}

        QPushButton {{
            background: {COLORS['panel']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            color: {COLORS['secondary']};
            padding: 9px 13px;
        }}

        QPushButton:hover {{
            background: {COLORS['panel_soft']};
            border-color: {COLORS['border_hover']};
            color: {COLORS['primary']};
        }}

        QPushButton:pressed {{
            background: {COLORS['card_hover']};
        }}

        QPushButton:disabled {{
            color: {COLORS['muted']};
            background: {COLORS['background_soft']};
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 2px 0 2px 2px;
        }}

        QScrollBar::handle:vertical {{
            background: {COLORS['border']};
            border-radius: 5px;
            min-height: 40px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {COLORS['muted']};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 10px;
        }}

        QScrollBar::handle:horizontal {{
            background: {COLORS['border']};
            border-radius: 5px;
            min-width: 40px;
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """


def card_stylesheet():
    return f"""
        QFrame {{
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
        }}

        QFrame:hover {{
            background: {COLORS['card_hover']};
            border-color: {COLORS['border_hover']};
        }}
    """


def muted_label_stylesheet():
    return (
        f"color: {COLORS['muted']}; "
        f"font-size: {FONT_SIZES['subtitle']}px;"
    )