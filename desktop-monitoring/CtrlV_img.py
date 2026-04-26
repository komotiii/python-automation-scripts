"""Save clipboard images with the active window title in the filename."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageGrab
from dotenv import load_dotenv
import win32gui


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SAVE_DIR_IMG = Path(os.getenv("CLIPBOARD_IMAGE_DIR", "images"))
POLL_INTERVAL_SECONDS = int(os.getenv("CLIPBOARD_IMAGE_POLL_INTERVAL_SECONDS", "5"))


def sanitize_filename(filename: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def get_active_window_title() -> str:
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)


def image_to_hash(image: Image.Image) -> str:
    with BytesIO() as buffer:
        image.save(buffer, format="PNG")
        return hashlib.md5(buffer.getvalue()).hexdigest()


def save_clipboard_image(last_image_hash: str | None = None) -> str | None:
    img = ImageGrab.grabclipboard()
    if isinstance(img, Image.Image):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        active_window = get_active_window_title()
        sanitized_window_title = sanitize_filename(active_window)
        filename = f"{timestamp}_{sanitized_window_title}.png"
        filepath = SAVE_DIR_IMG / filename

        current_image_hash = image_to_hash(img)
        if current_image_hash == last_image_hash:
            return last_image_hash

        try:
            SAVE_DIR_IMG.mkdir(parents=True, exist_ok=True)
            img.save(filepath, "PNG")
            logging.info("Saved image: %s", filepath)
        except Exception as exc:
            logging.error("Error while saving the image: %s", exc)

        return current_image_hash

    return last_image_hash


def monitor_clipboard() -> None:
    last_image_hash = None
    while True:
        last_image_hash = save_clipboard_image(last_image_hash)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    monitor_clipboard()
