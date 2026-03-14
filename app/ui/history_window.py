"""
History window: shows execution history, per-scenario stats, and report export.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Optional

from app.data.repository import get_runs, get_scenario_stats, delete_run
from app.data.reporter import generate_html_report
from app.core.logger_service import get_logger

logger = get_logger(__name__)


class HistoryWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("SkyjarBot — Run History")
        self.resizable(True, True)
        self.geometry("860x480")
        self._build_ui()
        self._load_runs()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 6, "pady": 4}

        # toolbar
        bar = ttk.Frame(self)
        bar.pack(fill="x", **pad)

        ttk.Button(bar, text="Refresh", command=self._load_runs).pack(side="left", padx=2)
        ttk.Button(bar, text="Delete selected", command=self._delete_selected).pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar, text="Report: all", command=lambda: self._report(None)).pack(side="left", padx=2)
        ttk.Button(bar, text="Report: selected scenario", command=self._report_selected).pack(side="left", padx=2)

        # runs table
        cols = ("id", "scenario", "started", "duration", "steps", "status")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        widths = {"id": 45, "scenario": 200, "started": 160, "duration": 80, "steps": 70, "status": 70}
        for c in cols:
            self._tree.heading(c, text=c.title())
            self._tree.column(c, width=widths[c], anchor="center" if c not in ("scenario",) else "w")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4, padx=(0, 6))

        self._tree.tag_configure("pass", foreground="#2a7a2a")
        self._tree.tag_configure("fail", foreground="#b00020")

        # stats panel
        stats_frame = ttk.LabelFrame(self, text="Scenario Stats")
        stats_frame.pack(fill="x", padx=6, pady=(0, 6))
        self._stats_var = tk.StringVar(value="Select a run to see scenario stats.")
        ttk.Label(stats_frame, textvariable=self._stats_var, justify="left",
                  font=("Consolas", 9)).pack(anchor="w", padx=8, pady=4)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_runs(self) -> None:
        for row in self._tree.get_children():
            self._tree.delete(row)
        try:
            runs = get_runs(100)
        except Exception as e:
            messagebox.showerror("DB Error", str(e), parent=self)
            return

        for r in runs:
            started = r.started_at.strftime("%Y-%m-%d %H:%M:%S") if r.started_at else "—"
            duration = f"{r.duration_s:.1f}s" if r.duration_s is not None else "—"
            status = "PASS" if r.success else "FAIL"
            tag = "pass" if r.success else "fail"
            self._tree.insert("", "end", iid=str(r.id), tags=(tag,),
                              values=(r.id, r.scenario_name, started, duration,
                                      f"{r.steps_done}/{r.total_steps}", status))

    def _on_select(self, _event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        run_id = int(sel[0])
        rows = self._tree.item(run_id, "values")
        scenario_name = rows[1]
        try:
            stats = get_scenario_stats(scenario_name)
            text = (
                f"Scenario: {scenario_name}    "
                f"Runs: {stats['total_runs']}    "
                f"Pass: {stats['successes']}    "
                f"Fail: {stats['failures']}    "
                f"Success rate: {stats['success_rate']}%    "
                f"Avg duration: {stats['avg_duration_s']}s"
            )
            self._stats_var.set(text)
        except Exception as e:
            self._stats_var.set(f"Error: {e}")

    def _delete_selected(self) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        run_id = int(sel[0])
        if messagebox.askyesno("Confirm", f"Delete run #{run_id}?", parent=self):
            try:
                delete_run(run_id)
                self._load_runs()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)

    def _report(self, scenario_name: Optional[str]) -> None:
        try:
            path = generate_html_report(scenario_name)
            webbrowser.open(path.as_uri())
            logger.info("Report opened: %s", path)
        except Exception as e:
            messagebox.showerror("Report Error", str(e), parent=self)

    def _report_selected(self) -> None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a run first.", parent=self)
            return
        scenario_name = self._tree.item(sel[0], "values")[1]
        self._report(scenario_name)
