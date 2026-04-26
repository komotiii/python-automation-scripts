"""Plot and log real-time network speed."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import psutil


CSV_FILENAME = Path(os.getenv("NETWORK_SPEED_CSV", "network_speed.csv"))
SAMPLE_INTERVAL_MS = int(os.getenv("NETWORK_SPEED_INTERVAL_MS", "1000"))

fig, ax = plt.subplots()
send_data = []
recv_data = []
time_points = []


def ensure_csv_header() -> None:
    if not CSV_FILENAME.exists():
        with CSV_FILENAME.open("w", newline="", encoding="utf-8") as csvfile:
            csv.writer(csvfile).writerow(["timestamp", "elapsed_seconds", "send_mbps", "recv_mbps"])


def update(frame: int):
    net_io = psutil.net_io_counters()
    current_time = frame
    if not time_points:
        update.initial_sent = net_io.bytes_sent
        update.initial_recv = net_io.bytes_recv
        send_speed = 0
        recv_speed = 0
    else:
        send_speed = (net_io.bytes_sent - update.initial_sent) * 8 / (1024 * 1024)
        recv_speed = (net_io.bytes_recv - update.initial_recv) * 8 / (1024 * 1024)

    update.initial_sent = net_io.bytes_sent
    update.initial_recv = net_io.bytes_recv

    time_points.append(current_time)
    send_data.append(send_speed)
    recv_data.append(recv_speed)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with CSV_FILENAME.open("a", newline="", encoding="utf-8") as csvfile:
        csv.writer(csvfile).writerow([timestamp, current_time, send_speed, recv_speed])

    ax.clear()
    ax.plot(time_points, send_data, label="Send Speed (Mbps)", color="orange")
    ax.plot(time_points, recv_data, label="Receive Speed (Mbps)", color="blue")
    ax.set_xlim(left=0, right=max(10, current_time))
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Speed (Mbps)")
    ax.set_title("Real-Time Network Speed")
    ax.legend()
    ax.grid()


update.initial_sent = 0
update.initial_recv = 0
ensure_csv_header()
ani = animation.FuncAnimation(fig, update, interval=SAMPLE_INTERVAL_MS)
plt.show()
