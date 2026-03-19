"""
Main window — PySide6 version.
Replaces the Tkinter main_window.py.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QTextEdit, QSplitter, QStatusBar,
    QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QFont, QColor

from app.core.models import Scenario, Step
from app.core.recorder import Recorder
from app.core.scenario_engine import ScenarioEngine
from app.core.serializer import save_scenario
from app.core.logger_service import get_logger
from app.ui.block_editor.block_editor_panel import BlockEditorPanel

logger = get_logger(__name__)

_SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "data" / "scenarios"
_SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

_LOGO_PATH = Path(__file__).resolve().parent.parent / "images" / "logo.jpg"


class MainWindowQt(QMainWindow):
    # Thread-safe signals for callbacks from recorder / player threads
    _sig_step_recorded = Signal(object)   # Step
    _sig_step_start    = Signal(int, object)
    _sig_step_done     = Signal(int, object)
    _sig_finished      = Signal(bool)

    def __init__(self):
        super().__init__()
        self._current_scenario: Optional[Scenario] = None
        self._prev_highlighted: int = -1

        self._recorder = Recorder(on_step_recorded=self._on_step_recorded)
        self._engine = ScenarioEngine(
            on_step_start=self._on_step_start,
            on_step_done=self._on_step_done,
            on_finished=self._on_finished,
        )

        # Connect thread-safe signals → UI slots
        self._sig_step_recorded.connect(self._handle_step_recorded)
        self._sig_step_start.connect(self._handle_step_start)
        self._sig_step_done.connect(self._handle_step_done)
        self._sig_finished.connect(self._handle_finished)

        self._setup_window()
        self._setup_toolbar()
        self._setup_central()
        self._setup_statusbar()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("SkyjarBot")
        self.resize(1100, 720)
        self.setMinimumSize(800, 560)
        self.setStyleSheet(_APP_STYLE)

        if _LOGO_PATH.exists():
            try:
                self.setWindowIcon(QIcon(str(_LOGO_PATH)))
            except Exception:
                pass

    def _setup_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setStyleSheet("""
            QToolBar {
                background: #E4EAFF;
                border-bottom: 1px solid #C8D4F0;
                spacing: 4px;
                padding: 4px 8px;
            }
            QToolButton {
                background: white;
                border: 1px solid #C8D4F0;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                color: #3A4A70;
            }
            QToolButton:hover { background: #D8E4FF; border-color: #A0B8E8; }
            QToolButton:pressed { background: #C0D4FF; }
            QToolButton:disabled { color: #AABBCC; background: #F0F4FA; }
        """)
        self.addToolBar(tb)

        self._act_record = QAction("⏺  Record", self)
        self._act_record.setCheckable(True)
        self._act_record.triggered.connect(self._toggle_record)
        tb.addAction(self._act_record)

        self._act_play = QAction("▶  Play", self)
        self._act_play.setCheckable(True)
        self._act_play.setEnabled(False)
        self._act_play.triggered.connect(self._toggle_play)
        tb.addAction(self._act_play)

        tb.addSeparator()

        save_act = QAction("💾  Save", self)
        save_act.triggered.connect(self._save)
        tb.addAction(save_act)

        load_act = QAction("📂  Load", self)
        load_act.triggered.connect(self._load)
        tb.addAction(load_act)

        clear_act = QAction("🗑  Clear", self)
        clear_act.triggered.connect(self._clear)
        tb.addAction(clear_act)

        tb.addSeparator()

        history_act = QAction("📊  History", self)
        history_act.triggered.connect(self._open_history)
        tb.addAction(history_act)

        parallel_act = QAction("⚡  Parallel", self)
        parallel_act.triggered.connect(self._open_parallel)
        tb.addAction(parallel_act)

    def _setup_central(self) -> None:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("QSplitter::handle { background: #D0DAF5; }")

        # Left: block editor
        self._editor = BlockEditorPanel()
        splitter.addWidget(self._editor)

        # Right: log panel
        log_frame = QWidget()
        log_frame.setMinimumWidth(220)
        log_frame.setMaximumWidth(320)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(0)

        log_title = QLabel("  Log")
        log_title.setFixedHeight(30)
        log_title.setStyleSheet("""
            QLabel {
                background: #E4EAFF;
                border-bottom: 1px solid #C8D4F0;
                font-size: 11px;
                font-weight: 700;
                color: rgba(0,0,0,0.5);
                letter-spacing: 1px;
            }
        """)
        log_layout.addWidget(log_title)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 9))
        self._log_text.setStyleSheet("""
            QTextEdit {
                background: #FAFCFF;
                border: none;
                color: #334;
            }
        """)
        log_layout.addWidget(self._log_text)
        splitter.addWidget(log_frame)

        splitter.setSizes([820, 280])
        self.setCentralWidget(splitter)

    def _setup_statusbar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet("""
            QStatusBar {
                background: #E8EEF8;
                border-top: 1px solid #D0DAF5;
                font-size: 11px;
                color: #556;
            }
        """)
        self._status_lbl = QLabel("Idle")
        sb.addWidget(self._status_lbl)
        self.setStatusBar(sb)

    # ── Toolbar actions ───────────────────────────────────────────────────────

    def _toggle_record(self, checked: bool) -> None:
        if checked:
            self._editor.clear()
            self._current_scenario = None
            self._recorder.start()
            self._act_record.setText("⏹  Stop")
            self._act_play.setEnabled(False)
            self._set_status("Recording…  (press Stop to finish)")
            self._log("Recording started.")
        else:
            self._recorder.stop()
            steps = self._recorder.steps
            self._current_scenario = Scenario(name="recorded", steps=steps)
            self._act_record.setText("⏺  Record")
            self._act_play.setEnabled(len(steps) > 0)
            self._set_status(f"Recording stopped.  {len(steps)} steps captured.")
            self._log(f"Recording stopped. {len(steps)} steps.")

    def _toggle_play(self, checked: bool) -> None:
        if checked:
            # Sync scenario from editor
            steps = self._editor.get_steps()
            if not steps:
                QMessageBox.warning(self, "Nothing to play",
                                    "No steps to play. Record or load a scenario first.")
                self._act_play.setChecked(False)
                return
            self._current_scenario = Scenario(
                name=getattr(self._current_scenario, "name", "scenario"),
                steps=steps,
            )
            self._engine.load_scenario(self._current_scenario)
            self._engine.run()
            self._act_play.setText("⏹  Stop")
            self._set_status(f"Playing '{self._current_scenario.name}'…")
        else:
            self._engine.stop()
            self._act_play.setText("▶  Play")
            self._set_status("Playback stopped.")

    def _save(self) -> None:
        steps = self._editor.get_steps()
        if not steps:
            QMessageBox.warning(self, "Nothing to save", "No steps to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Scenario", str(_SCENARIOS_DIR),
            "JSON files (*.json)",
        )
        if path:
            sc = self._current_scenario or Scenario(name="scenario", steps=steps)
            sc.steps = steps
            save_scenario(sc, path)
            self._log(f"Saved → {path}")
            self._set_status(f"Saved: {Path(path).name}")

    def _load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Scenario", str(_SCENARIOS_DIR),
            "JSON files (*.json)",
        )
        if path:
            try:
                sc = self._engine.load_from_file(path)
                self._current_scenario = sc
                self._editor.load_steps(sc.steps)
                self._act_play.setEnabled(True)
                self._set_status(f"Loaded '{sc.name}'  ({len(sc.steps)} steps)")
                self._log(f"Loaded: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Load error", str(e))

    def _clear(self) -> None:
        if self._engine.is_running:
            self._engine.stop()
        self._recorder.stop()
        self._act_record.setChecked(False)
        self._act_record.setText("⏺  Record")
        self._act_play.setChecked(False)
        self._act_play.setText("▶  Play")
        self._act_play.setEnabled(False)
        self._current_scenario = None
        self._editor.clear()
        self._set_status("Cleared.")
        self._log("Cleared.")

    def _open_history(self) -> None:
        try:
            import tkinter as tk
            from app.ui.history_window import HistoryWindow
            root = tk.Tk()
            root.withdraw()
            HistoryWindow(root)
            root.mainloop()
        except Exception as e:
            QMessageBox.information(self, "History", f"History viewer: {e}")

    def _open_parallel(self) -> None:
        try:
            import tkinter as tk
            from app.ui.parallel_runner_window import ParallelRunnerWindow
            root = tk.Tk()
            root.withdraw()
            ParallelRunnerWindow(root)
            root.mainloop()
        except Exception as e:
            QMessageBox.information(self, "Parallel", f"Parallel runner: {e}")

    # ── Thread callbacks → signals → UI slots ─────────────────────────────────

    def _on_step_recorded(self, step: Step) -> None:
        self._sig_step_recorded.emit(step)

    def _on_step_start(self, index: int, step: Step) -> None:
        self._sig_step_start.emit(index, step)

    def _on_step_done(self, index: int, step: Step) -> None:
        self._sig_step_done.emit(index, step)

    def _on_finished(self, success: bool) -> None:
        self._sig_finished.emit(success)

    def _handle_step_recorded(self, step: Step) -> None:
        self._editor.add_step(step)

    def _handle_step_start(self, index: int, step: Step) -> None:
        if self._prev_highlighted >= 0:
            self._editor.highlight_step(self._prev_highlighted, False)
        self._editor.highlight_step(index, True)
        self._prev_highlighted = index

    def _handle_step_done(self, index: int, step: Step) -> None:
        pass  # could log here

    def _handle_finished(self, success: bool) -> None:
        if self._prev_highlighted >= 0:
            self._editor.highlight_step(self._prev_highlighted, False)
            self._prev_highlighted = -1
        self._act_play.setChecked(False)
        self._act_play.setText("▶  Play")
        msg = "Playback complete." if success else "Playback stopped / failed."
        self._set_status(msg)
        self._log(msg)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, text: str) -> None:
        self._status_lbl.setText(text)

    def _log(self, text: str) -> None:
        self._log_text.append(text)


# ── Global app stylesheet ─────────────────────────────────────────────────────

_APP_STYLE = """
QMainWindow, QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}
QToolTip {
    background: #FFFBE6;
    border: 1px solid #E0C060;
    color: #444;
    padding: 3px 6px;
    border-radius: 4px;
}
"""
