"""
Parallel Runner window: load multiple scenarios and run them simultaneously.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from app.core.parallel_runner import ParallelRunner, RunSlot
from app.core.logger_service import get_logger

logger = get_logger(__name__)

_STATUS_COLORS = {
    "pending": "#888888",
    "running": "#0055cc",
    "passed":  "#2a7a2a",
    "failed":  "#b00020",
    "stopped": "#cc6600",
}


class ParallelRunnerWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("SkyjarBot — Parallel Runner")
        self.geometry("720x420")
        self.resizable(True, True)
        self._runner = ParallelRunner()
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 6, "pady": 4}

        # toolbar
        bar = ttk.Frame(self)
        bar.pack(fill="x", **pad)
        ttk.Button(bar, text="Add scenario…",  command=self._add_scenario).pack(side="left", padx=2)
        ttk.Button(bar, text="Remove selected", command=self._remove_selected).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=8)
        self._btn_run  = ttk.Button(bar, text="▶  Run all", command=self._run_all)
        self._btn_run.pack(side="left", padx=2)
        self._btn_stop = ttk.Button(bar, text="⏹  Stop all", command=self._stop_all, state="disabled")
        self._btn_stop.pack(side="left", padx=2)

        # scenario table
        cols = ("scenario", "path", "status", "error")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        widths = {"scenario": 180, "path": 300, "status": 80, "error": 220}
        for c in cols:
            self._tree.heading(c, text=c.title())
            self._tree.column(c, width=widths[c],
                              anchor="w" if c in ("scenario", "path", "error") else "center")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4, padx=(0, 6))

        for s, color in _STATUS_COLORS.items():
            self._tree.tag_configure(s, foreground=color)

        # status bar
        self._status_var = tk.StringVar(value="Add scenarios, then click Run all.")
        ttk.Label(self, textvariable=self._status_var, anchor="w",
                  relief="sunken").pack(fill="x", padx=6, pady=(0, 4))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_scenario(self) -> None:
        paths = filedialog.askopenfilenames(
            filetypes=[("JSON scenarios", "*.json")],
            title="Select scenario files",
            parent=self,
        )
        for path in paths:
            try:
                slot = self._runner.add_scenario_file(
                    path,
                    on_status_change=self._on_slot_change,
                )
                self._tree.insert(
                    "", "end", iid=str(id(slot)),
                    tags=("pending",),
                    values=(slot.scenario.name, path, "pending", ""),
                )
            except Exception as e:
                messagebox.showerror("Load error", f"{path}:\n{e}", parent=self)

    def _remove_selected(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        # Rebuild runner without the removed slot
        iid = sel[0]
        self._tree.delete(iid)
        # Rebuild runner slots from remaining tree rows
        self._runner.clear()
        for row_iid in self._tree.get_children():
            path = self._tree.item(row_iid, "values")[1]
            try:
                self._runner.add_scenario_file(path, on_status_change=self._on_slot_change)
            except Exception:
                pass

    def _run_all(self) -> None:
        if not self._runner.slots:
            messagebox.showinfo("No scenarios", "Add at least one scenario first.", parent=self)
            return
        # Reset statuses
        for iid in self._tree.get_children():
            self._tree.item(iid, tags=("pending",), values=(
                *self._tree.item(iid, "values")[:2], "pending", ""
            ))
        self._btn_run.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._status_var.set(f"Running {len(self._runner.slots)} scenario(s)…")
        self._runner.run_all(on_all_done=self._on_all_done)

    def _stop_all(self) -> None:
        self._runner.stop_all()
        self._btn_run.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._status_var.set("Stopped.")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_slot_change(self, slot: RunSlot) -> None:
        iid = str(id(slot))
        self.after(0, lambda: self._update_row(iid, slot))

    def _update_row(self, iid: str, slot: RunSlot) -> None:
        if not self._tree.exists(iid):
            return
        vals = self._tree.item(iid, "values")
        self._tree.item(iid,
                        tags=(slot.status,),
                        values=(vals[0], vals[1], slot.status, slot.error))

    def _on_all_done(self, slots: list[RunSlot]) -> None:
        passed  = sum(1 for s in slots if s.status == "passed")
        failed  = sum(1 for s in slots if s.status == "failed")
        self.after(0, lambda: self._status_var.set(
            f"Done — {passed} passed, {failed} failed."
        ))
        self.after(0, lambda: self._btn_run.config(state="normal"))
        self.after(0, lambda: self._btn_stop.config(state="disabled"))
