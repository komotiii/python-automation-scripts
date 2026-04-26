"""Log the active window title when it changes."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path

import win32gui
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LOG_FILE = Path(os.getenv("ACTIVE_WINDOW_LOG_FILE", "active_window_log.txt"))
POLL_INTERVAL_SECONDS = int(os.getenv("ACTIVE_WINDOW_POLL_INTERVAL_SECONDS", "1"))


def get_active_window_info() -> tuple[str, str]:
    active_window_handle = win32gui.GetForegroundWindow()
    window_title = win32gui.GetWindowText(active_window_handle)
    return window_title, datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_log(line: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    window_title, start_time = get_active_window_info()
    append_log(f"{start_time} {window_title}")
    print(f"{start_time} {window_title}")

    previous_window_title = window_title
    while True:
        window_title, change_time = get_active_window_info()
        if window_title != previous_window_title:
            print(f"{change_time} {window_title}")
            append_log(f"{change_time} {window_title}")
            previous_window_title = window_title
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
    input("Press Enter to exit...")
