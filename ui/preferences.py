from PySide6.QtCore import QSettings


_DEFAULTS = {
    "accent": "#ff9f43",
    "accent_hover": "#ffb765",
    "background": "#0a0b0e",
    "surface": "#13161c",
    "surface_hover": "#202631",
    "card": "#12151b",
    "card_hover": "#1a1f27",
    "font_size": 13,
    "card_size": 210,
    "card_gap": 24,
    "corner_radius": 12,
    "hover_highlight": True,
    "resize_animation": True,
    "animation_speed": 260,
    "maximized": True,
}


def settings():
    return QSettings("NekoTrack", "NekoTrack")


def get(key):
    default = _DEFAULTS[key]
    value = settings().value(key, default)
    if isinstance(default, bool):
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)
    if isinstance(default, int):
        try:
            return max(1, int(value)) if key == "font_size" else int(value)
        except (TypeError, ValueError):
            return default
    return value


def set_value(key, value):
    settings().setValue(key, value)
    settings().sync()


def defaults():
    return dict(_DEFAULTS)


def reset():
    qsettings = settings()
    qsettings.clear()
    qsettings.sync()
