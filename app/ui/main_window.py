"""
Main UI window built with Tkinter.
Thin layer — all logic is delegated to core modules.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

from app.core.models import Scenario, Step
from app.core.recorder import Recorder
from app.core.scenario_engine import ScenarioEngine
from app.core.serializer import save_scenario
from app.core.logger_service import get_logger

logger = get_logger(__name__)

_SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data" / "scenarios"
_SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


class MainWindow:
    def __init__(self, root: tk.Tk):
        self._root = root
        self._root.title("SkyjarBot — Macro Recorder")
        self._root.resizable(False, False)

        self._recorder = Recorder(on_step_recorded=self._on_step_recorded)
        self._engine = ScenarioEngine(
            on_step_start=self._on_step_start,
            on_step_done=self._on_step_done,
            on_finished=self._on_finished,
        )
        self._current_scenario: Optional[Scenario] = None

        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # ── Top bar: record / playback controls
        ctrl = ttk.LabelFrame(self._root, text="Controls")
        ctrl.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)

        self._btn_record = ttk.Button(ctrl, text="⏺  Record", width=14, command=self._toggle_record)
        self._btn_record.grid(row=0, column=0, **pad)

        self._btn_play = ttk.Button(ctrl, text="▶  Play", width=14, command=self._toggle_play, state="disabled")
        self._btn_play.grid(row=0, column=1, **pad)

        ttk.Button(ctrl, text="💾  Save", width=14, command=self._save).grid(row=0, column=2, **pad)
        ttk.Button(ctrl, text="📂  Load", width=14, command=self._load).grid(row=0, column=3, **pad)
        ttk.Button(ctrl, text="🗑  Clear", width=14, command=self._clear).grid(row=0, column=4, **pad)

        # ── Status bar
        self._status_var = tk.StringVar(value="Idle")
        ttk.Label(self._root, textvariable=self._status_var, anchor="w", relief="sunken").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=2
        )

        # ── Steps list
        steps_frame = ttk.LabelFrame(self._root, text="Recorded Steps")
        steps_frame.grid(row=2, column=0, sticky="nsew", **pad)

        self._steps_list = tk.Listbox(steps_frame, width=55, height=20, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(steps_frame, orient="vertical", command=self._steps_list.yview)
        self._steps_list.configure(yscrollcommand=scrollbar.set)
        self._steps_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Log panel
        log_frame = ttk.LabelFrame(self._root, text="Log")
        log_frame.grid(row=2, column=1, sticky="nsew", **pad)

        self._log_text = tk.Text(log_frame, width=40, height=20, font=("Consolas", 9), state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scroll.set)
        self._log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        self._root.columnconfigure(0, weight=1)
        self._root.columnconfigure(1, weight=1)

    # ── Controls ──────────────────────────────────────────────────────────────

    def _toggle_record(self) -> None:
        if self._recorder._recording:
            self._recorder.stop()
            steps = self._recorder.steps
            self._current_scenario = Scenario(name="recorded", steps=steps)
            self._btn_record.config(text="⏺  Record")
            self._btn_play.config(state="normal")
            self._set_status(f"Stopped recording. {len(steps)} steps captured.")
            self._log(f"Recording stopped. {len(steps)} steps.")
        else:
            self._steps_list.delete(0, tk.END)
            self._recorder.start()
            self._btn_record.config(text="⏹  Stop")
            self._btn_play.config(state="disabled")
            self._set_status("Recording… (press Stop to finish)")
            self._log("Recording started.")

    def _toggle_play(self) -> None:
        if self._engine.is_running:
            self._engine.stop()
            self._btn_play.config(text="▶  Play")
            self._set_status("Playback stopped.")
        else:
            if not self._current_scenario or not self._current_scenario.steps:
                messagebox.showwarning("No steps", "Nothing to play. Record or load a scenario first.")
                return
            self._engine.load_scenario(self._current_scenario)
            self._engine.run()
            self._btn_play.config(text="⏹  Stop")
            self._set_status(f"Playing '{self._current_scenario.name}'…")

    def _save(self) -> None:
        if not self._current_scenario or not self._current_scenario.steps:
            messagebox.showwarning("Nothing to save", "No steps recorded.")
            return
        path = filedialog.asksaveasfilename(
            initialdir=str(_SCENARIOS_DIR),
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Scenario",
        )
        if path:
            save_scenario(self._current_scenario, path)
            self._log(f"Saved to {path}")
            self._set_status(f"Saved: {Path(path).name}")

    def _load(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(_SCENARIOS_DIR),
            filetypes=[("JSON files", "*.json")],
            title="Load Scenario",
        )
        if path:
            try:
                self._current_scenario = self._engine.load_from_file(path)
                self._steps_list.delete(0, tk.END)
                for i, step in enumerate(self._current_scenario.steps):
                    self._steps_list.insert(tk.END, f"[{i:03d}] {_describe_step(step)}")
                self._btn_play.config(state="normal")
                self._set_status(f"Loaded '{self._current_scenario.name}' ({len(self._current_scenario.steps)} steps)")
                self._log(f"Loaded scenario from {path}")
            except Exception as e:
                messagebox.showerror("Load error", str(e))

    def _clear(self) -> None:
        if self._engine.is_running:
            self._engine.stop()
        self._recorder.stop()
        self._current_scenario = None
        self._steps_list.delete(0, tk.END)
        self._btn_record.config(text="⏺  Record")
        self._btn_play.config(state="disabled")
        self._set_status("Cleared.")
        self._log("Cleared.")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_step_recorded(self, step: Step) -> None:
        idx = len(self._recorder.steps) - 1
        self._root.after(0, lambda: self._steps_list.insert(tk.END, f"[{idx:03d}] {_describe_step(step)}"))

    def _on_step_start(self, index: int, step: Step) -> None:
        self._root.after(0, lambda: self._steps_list.selection_clear(0, tk.END))
        self._root.after(0, lambda: self._steps_list.selection_set(index))
        self._root.after(0, lambda: self._steps_list.see(index))

    def _on_step_done(self, index: int, step: Step) -> None:
        self._log(f"Step {index:03d} done: {_describe_step(step)}")

    def _on_finished(self, success: bool) -> None:
        msg = "Playback complete." if success else "Playback stopped/failed."
        self._root.after(0, lambda: self._btn_play.config(text="▶  Play"))
        self._root.after(0, lambda: self._set_status(msg))
        self._root.after(0, lambda: self._log(msg))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, text: str) -> None:
        self._status_var.set(text)

    def _log(self, text: str) -> None:
        self._log_text.config(state="normal")
        self._log_text.insert(tk.END, text + "\n")
        self._log_text.see(tk.END)
        self._log_text.config(state="disabled")


# ── Step description helper ───────────────────────────────────────────────────

def _describe_step(step) -> str:
    from app.core.models import ActionStep, ConditionStep, DelayStep, ActionType
    if isinstance(step, DelayStep):
        return f"delay {step.duration_ms} ms"
    if isinstance(step, ActionStep):
        t = step.action_type
        if t == ActionType.MOUSE_CLICK:
            return f"click ({step.x}, {step.y}) [{step.button}]"
        if t == ActionType.MOUSE_MOVE:
            return f"move ({step.x}, {step.y})"
        if t == ActionType.MOUSE_SCROLL:
            return f"scroll ({step.x}, {step.y}) dx={step.dx} dy={step.dy}"
        if t == ActionType.KEY_PRESS:
            return f"key_press [{step.key}]"
        if t == ActionType.TYPE_TEXT:
            return f"type '{step.text}'"
    if isinstance(step, ConditionStep):
        return f"pixel_condition ({step.x},{step.y}) == {step.expected_color}"
    return repr(step)
