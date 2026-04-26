"""Collect typing test results from clipboard and export them to CSV."""

from __future__ import annotations

import csv
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import pyperclip
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CSV_PATH = Path(os.getenv("TYPING_MONITOR_CSV_PATH", "typing_data.csv"))
SESSION_SECONDS = int(os.getenv("TYPING_MONITOR_SESSION_SECONDS", "300"))
POLL_INTERVAL_SECONDS = int(os.getenv("TYPING_MONITOR_POLL_INTERVAL_SECONDS", "1"))

data_records: list[dict[str, object]] = []
end_time_flag = False


def save_to_csv(wpm: float, accuracy: float, characters: int, errors: int, time_taken: str) -> None:
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if wpm == 0.0:
        return

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = CSV_PATH.exists()
    with CSV_PATH.open(mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["datetime", "wpm", "accuracy", "characters", "errors", "time"])
        writer.writerow([current_datetime, wpm, accuracy, characters, errors, time_taken])

    data_records.append(
        {
            "datetime": current_datetime,
            "wpm": wpm,
            "accuracy": accuracy,
            "characters": characters,
            "errors": errors,
            "time": time_taken,
        }
    )


def extract_data(input_data: str) -> None:
    wpm_match = re.search(r"(\d+(\.\d+)?)wpm", input_data)
    accuracy_match = re.search(r"(\d+\.\d+)%", input_data)
    characters_match = re.search(r"Characters:(\d+)", input_data)
    errors_match = re.search(r"Errors:(\d+)", input_data)
    time_match = re.search(r"Time:(\d{2}:\d{2}:\d{2}\.\d{2})", input_data)

    if not wpm_match:
        return

    wpm = float(wpm_match.group(1))
    accuracy = float(accuracy_match.group(1)) if accuracy_match else 0.0
    characters = int(characters_match.group(1)) if characters_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0
    time_taken = time_match.group(1) if time_match else "00:00:00.00"

    print(
        f"Recorded Data: WPM: {wpm}, Accuracy: {accuracy:.2f}%, Characters: {characters}, Errors: {errors}, Time: {time_taken}"
    )
    save_to_csv(wpm, accuracy, characters, errors, time_taken)


def timer_thread() -> None:
    global end_time_flag
    time.sleep(SESSION_SECONDS)
    print(f"{SESSION_SECONDS // 60} minutes are up!")
    end_time_flag = True


def monitor_clipboard() -> None:
    previous_clipboard = ""
    while True:
        clipboard_content = pyperclip.paste()
        if clipboard_content != previous_clipboard:
            extract_data(clipboard_content)
            previous_clipboard = clipboard_content
        if end_time_flag:
            print("No further data extraction.")
            break
        time.sleep(POLL_INTERVAL_SECONDS)


def display_analysis() -> None:
    if not data_records:
        print("No data to analyze.")
        return

    total_wpm = sum(record["wpm"] for record in data_records)
    total_accuracy = sum(record["accuracy"] for record in data_records)
    total_characters = sum(record["characters"] for record in data_records)
    total_errors = sum(record["errors"] for record in data_records)
    average_wpm = total_wpm / len(data_records)
    average_accuracy = total_accuracy / len(data_records)

    print("\n------------- Results -------------")
    print(f"{'Total Typing Sessions:':<25} {len(data_records):>5}")
    print(f"{'Total Characters Typed:':<25} {total_characters:>5}")
    print(f"{'Total Errors:':<25} {total_errors:>5}")
    print(f"{'Average WPM:':<25} {average_wpm:>5.2f}")
    print(f"{'Average Accuracy:':<25} {average_accuracy:>5.2f}%")
    print("-" * 35)


monitor_thread = threading.Thread(target=monitor_clipboard, daemon=True)
monitor_thread.start()

session_timer = threading.Thread(target=timer_thread, daemon=True)
session_timer.start()

while not end_time_flag:
    time.sleep(1)

display_analysis()
