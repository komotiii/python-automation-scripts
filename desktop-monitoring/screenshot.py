"""Capture a single screenshot and save it locally."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import ImageGrab


def take_screenshot() -> Path:
    now = datetime.now()
    file_name = Path(f"screenshot_{now.strftime('%Y-%m-%d_%H-%M-%S')}.png")
    screenshot = ImageGrab.grab()
    screenshot.save(file_name)
    print(f"Screenshot saved as {file_name}")
    return file_name


if __name__ == "__main__":
    take_screenshot()
