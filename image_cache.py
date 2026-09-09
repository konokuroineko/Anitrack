from pathlib import Path

import requests
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage


IMAGE_DIRECTORY = Path("data") / "images" / "works"


def download_cover(work_id, image_url):
    """Download and resize a work cover, returning its local path."""

    if not image_url:
        return None

    response = requests.get(
        image_url,
        timeout=15
    )
    response.raise_for_status()

    image = QImage()
    if not image.loadFromData(response.content):
        raise ValueError("Downloaded cover is not a supported image")

    image = image.scaled(
        400,
        600,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    image_path = IMAGE_DIRECTORY / f"{work_id}.jpg"

    if not image.save(str(image_path), "JPG", 85):
        raise OSError("Could not save cover image")

    return str(image_path)
