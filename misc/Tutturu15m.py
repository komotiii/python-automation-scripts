"""Quarter-hour reminder with configurable sound and anti-repeat guard."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path

import winsound
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

REMINDER_SOUND = Path(os.getenv("TUTTURU_SOUND_FILE", "totoru.wav"))
REMINDER_INTERVAL_SECONDS = int(os.getenv("TUTTURU_CHECK_INTERVAL_SECONDS", "1"))
SNOOZE_SECONDS = int(os.getenv("TUTTURU_SNOOZE_SECONDS", "890"))
ACTIVE_MINUTES = {0, 15, 30, 45}


def play_sound(sound_file: Path) -> None:
    if not sound_file.exists():
        winsound.MessageBeep()
        return
    winsound.PlaySound(str(sound_file), winsound.SND_FILENAME)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    last_trigger_key = None

    while True:
        now = datetime.now()
        minute_key = (now.year, now.month, now.day, now.hour, now.minute)

        if now.minute in ACTIVE_MINUTES and minute_key != last_trigger_key:
            last_trigger_key = minute_key
            message = f"{now.strftime('%H:%M')} - Tutturu!"
            logging.info(message)
            print(message)
            play_sound(REMINDER_SOUND)
            time.sleep(SNOOZE_SECONDS)
            continue

        time.sleep(REMINDER_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
