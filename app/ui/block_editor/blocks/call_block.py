"""Call Scenario block: run another scenario file inline."""
from __future__ import annotations
import os

from PySide6.QtWidgets import QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QLabel

from app.core.models import CallScenarioStep
from app.ui.block_editor.blocks.base_block import BaseBlock, style_input


class CallBlock(BaseBlock):
    HEADER_COLOR = "#D5F0F0"
    ICON = "📂"
    TYPE_LABEL = "CALL"

    def _build_body(self, layout: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = QLabel("File")
        lbl.setFixedWidth(70)
        lbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        row.addWidget(lbl)
        self._path_edit = style_input(QLineEdit())
        self._path_edit.setPlaceholderText("path/to/scenario.json")
        row.addWidget(self._path_edit)
        browse = QPushButton("📂")
        browse.setFixedSize(26, 26)
        browse.setStyleSheet("background:#EEF6FF; border:1px solid #C9DEF6; border-radius:5px;")
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        layout.addLayout(row)

        self._path_edit.textChanged.connect(self._emit_changed)

    def _browse(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        scenarios_dir = Path(__file__).resolve().parents[4] / "app" / "data" / "scenarios"
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Scenario", str(scenarios_dir), "JSON files (*.json)"
        )
        if path:
            self._path_edit.setText(path)

    def _emit_changed(self) -> None:
        self.update_description()
        self.changed.emit()

    def get_description(self) -> str:
        if not hasattr(self, "_path_edit"):
            return ""
        return os.path.basename(self._path_edit.text()) or "(none)"

    def to_step(self) -> CallScenarioStep:
        return CallScenarioStep(scenario_path=self._path_edit.text())

    def from_step(self, step: CallScenarioStep) -> None:
        self._path_edit.setText(step.scenario_path)
        self.update_description()
