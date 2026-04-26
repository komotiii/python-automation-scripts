"""Small startup launcher for running multiple Python scripts from one window.

Set `STARTUP_PROGRAMS` as a semicolon-separated list of script paths if you want
to override the default programs.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import List


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LAUNCH_DELAY_SECONDS = 5


@dataclass(frozen=True)
class ProgramSpec:
    path: Path

    @property
    def display_name(self) -> str:
        return self.path.name


def load_programs() -> List[ProgramSpec]:
    raw = os.getenv("STARTUP_PROGRAMS", "").strip()
    if raw:
        paths = [Path(item.strip()) for item in raw.split(";") if item.strip()]
    else:
        paths = [
            Path(r"C:\Users\name\Documents\GitHub\python-automation-scripts\api-bots\Tukunavi.py"),
            Path(r"C:\Users\name\Documents\GitHub\python-automation-scripts\misc\Tutturu15m.py")
        ]
    return [ProgramSpec(path=path) for path in paths]


class ProgramManager:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Program Manager")
        self.root.geometry("900x420")

        self.programs = load_programs()
        self.processes: List[subprocess.Popen[str] | None] = [None] * len(self.programs)
        self.status_labels: List[tk.Label] = []
        self.lamps: List[tk.Label] = []
        self.run_counts = [0] * len(self.programs)
        self.error_counts = [0] * len(self.programs)

        header = tk.Label(
            self.root,
            text="Startup Launcher",
            font=("Segoe UI", 14, "bold"),
        )
        header.pack(pady=(12, 6))

        hint = tk.Label(
            self.root,
            text="Click the circles to view output. Close this window to stop all programs.",
            font=("Segoe UI", 10),
        )
        hint.pack(pady=(0, 10))

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=12)

        self.text_box = tk.Text(self.root, height=10, width=110)
        self.text_box.pack(fill=tk.BOTH, expand=False, padx=12, pady=(0, 12))

        for index, program in enumerate(self.programs):
            lamp = tk.Label(self.frame, text="◯", fg="gray", font=("Arial", 18), width=2)
            lamp.grid(row=index, column=0, padx=6, pady=4)
            lamp.bind("<Button-1>", lambda _event, idx=index: self.show_output(idx))

            label = tk.Label(self.frame, anchor="w", justify="left")
            label.grid(row=index, column=1, sticky="w", padx=6, pady=4)
            self.lamps.append(lamp)
            self.status_labels.append(label)
            self._refresh_row(index, "waiting")

        Thread(target=self.start_all_programs, daemon=True).start()

    def _refresh_row(self, index: int, status: str) -> None:
        program = self.programs[index]
        lamp = self.lamps[index]
        label = self.status_labels[index]
        color = {
            "waiting": "gray",
            "running": "green",
            "error": "red",
            "missing": "orange",
            "finished": "blue",
        }.get(status, "gray")
        lamp.config(fg=color)
        label.config(
            text=f"{program.display_name} | {status} | runs: {self.run_counts[index]} | errors: {self.error_counts[index]}"
        )

    def _append_output(self, text: str) -> None:
        self.text_box.insert(tk.END, text + "\n")
        self.text_box.yview(tk.END)

    def start_all_programs(self) -> None:
        for index, program in enumerate(self.programs):
            if not program.path.exists():
                self.error_counts[index] += 1
                self.root.after(0, self._refresh_row, index, "missing")
                self.root.after(0, self._append_output, f"[missing] {program.path}")
                continue

            self.root.after(0, self._append_output, f"Starting: {program.path}")
            process = subprocess.Popen(
                [sys.executable, str(program.path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(program.path.parent),
            )
            self.processes[index] = process
            self.run_counts[index] += 1
            self.root.after(0, self._refresh_row, index, "running")

            Thread(target=self.capture_output, args=(index, process), daemon=True).start()
            if index < len(self.programs) - 1:
                time.sleep(DEFAULT_LAUNCH_DELAY_SECONDS)

    def capture_output(self, program_index: int, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None

        for line in process.stdout:
            self.root.after(0, self._append_output, f"[stdout] {self.programs[program_index].display_name}: {line.rstrip()}")

        return_code = process.wait()
        status = "finished" if return_code == 0 else "error"
        if return_code != 0:
            self.error_counts[program_index] += 1
        self.root.after(0, self._refresh_row, program_index, status)
        self.root.after(0, self._append_output, f"Finished: {self.programs[program_index].display_name} (code {return_code})")

    def show_output(self, program_index: int) -> None:
        process = self.processes[program_index]
        self.text_box.delete(1.0, tk.END)
        self._append_output(f"Selected: {self.programs[program_index].path}")
        self._append_output(f"Process running: {process is not None and process.poll() is None}")


if __name__ == "__main__":
    root = tk.Tk()
    ProgramManager(root)
    root.mainloop()
