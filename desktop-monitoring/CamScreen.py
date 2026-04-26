"""Capture webcam frames and screenshots on a fixed interval."""

from __future__ import annotations

import os
import time
from pathlib import Path

import cv2
import mss
import mss.tools
from dotenv import load_dotenv
from screeninfo import get_monitors


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SAVE_FOLDER_CAM = Path(os.getenv("CAMSCREEN_CAMERA_DIR", "cam"))
SAVE_FOLDER_SCREEN = Path(os.getenv("CAMSCREEN_SCREEN_DIR", "screen"))
WAIT_TIME_SECONDS = int(os.getenv("CAMSCREEN_INTERVAL_SECONDS", "600"))


def ensure_directories() -> None:
    SAVE_FOLDER_CAM.mkdir(parents=True, exist_ok=True)
    SAVE_FOLDER_SCREEN.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_directories()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    monitors = get_monitors()

    time.sleep(1)
    cap.read()

    try:
        print(f"Start monitoring. Interval: {WAIT_TIME_SECONDS}s.")
        with mss.mss() as sct:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read webcam frame.")
                    time.sleep(WAIT_TIME_SECONDS)
                    continue

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = SAVE_FOLDER_CAM / f"cam_{timestamp}.png"
                cv2.imwrite(str(filename), frame)
                print(f"Webcam saved: {filename}")

                for index, monitor in enumerate(monitors, start=1):
                    monitor_area = {"top": monitor.y, "left": monitor.x, "width": monitor.width, "height": monitor.height}
                    sct_img = sct.grab(monitor_area)
                    screenshot_filename = SAVE_FOLDER_SCREEN / f"scr_{timestamp}_{index}.png"
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(screenshot_filename))
                    print(f"Screen {index} saved: {screenshot_filename}")

                time.sleep(WAIT_TIME_SECONDS)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
