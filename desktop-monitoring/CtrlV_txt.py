"""Save clipboard text into a daily Excel log tagged with the active window."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path

import openpyxl
import pyperclip
import win32gui
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SAVE_DIR = Path(os.getenv("CLIPBOARD_TEXT_DIR", "text"))
POLL_INTERVAL_SECONDS = int(os.getenv("CLIPBOARD_TEXT_POLL_INTERVAL_SECONDS", "3"))


def get_active_window_title() -> str:
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)


def save_clipboard_text() -> None:
    content = pyperclip.paste()
    if not content:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    active_window = get_active_window_title()
    date_filename = datetime.now().strftime("%Y-%m-%d")
    filepath = SAVE_DIR / f"txt_{date_filename}.xlsx"

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    if filepath.exists():
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active
    else:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(["Timestamp", "Active Window", "Content"])

    sheet.append([timestamp, active_window, content])
    workbook.save(filepath)
    logging.info("Saved text: %s", filepath)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    previous_clipboard = None
    while True:
        current_clipboard = pyperclip.paste()
        if current_clipboard != previous_clipboard:
            save_clipboard_text()
            previous_clipboard = current_clipboard
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
