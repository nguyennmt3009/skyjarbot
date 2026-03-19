"""Delay block: wait N ms (with optional random range)."""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QSpinBox, QCheckBox, QWidget

from app.core.models import DelayStep
from app.ui.block_editor.blocks.base_block import BaseBlock, form_row, style_input


class DelayBlock(BaseBlock):
    HEADER_COLOR = "#E8DEFF"
    ICON = "⏱"
    TYPE_LABEL = "DELAY"

    def _build_body(self, layout: QVBoxLayout) -> None:
        self._min_spin = style_input(QSpinBox())
        self._min_spin.setRange(0, 999_999)
        self._min_spin.setValue(500)
        self._min_spin.setSuffix(" ms")
        layout.addLayout(form_row("Min", self._min_spin))

        self._random_check = QCheckBox("Random range")
        self._random_check.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.6);")
        layout.addWidget(self._random_check)

        self._max_widget = QWidget()
        self._max_spin = style_input(QSpinBox())
        self._max_spin.setRange(0, 999_999)
        self._max_spin.setValue(1000)
        self._max_spin.setSuffix(" ms")
        self._max_widget.setLayout(form_row("Max", self._max_spin))
        self._max_widget.setVisible(False)
        layout.addWidget(self._max_widget)

        self._random_check.toggled.connect(self._max_widget.setVisible)
        self._random_check.toggled.connect(self._emit_changed)
        self._min_spin.valueChanged.connect(self._emit_changed)
        self._max_spin.valueChanged.connect(self._emit_changed)

    def _emit_changed(self) -> None:
        self.update_description()
        self.changed.emit()

    def get_description(self) -> str:
        if not hasattr(self, "_min_spin"):
            return ""
        mn = self._min_spin.value()
        if self._random_check.isChecked():
            return f"{mn} – {self._max_spin.value()} ms (random)"
        return f"{mn} ms"

    def to_step(self) -> DelayStep:
        step = DelayStep(duration_ms=self._min_spin.value())
        if self._random_check.isChecked():
            step.duration_max_ms = self._max_spin.value()
        return step

    def from_step(self, step: DelayStep) -> None:
        self._min_spin.setValue(step.duration_ms)
        if step.duration_max_ms is not None and step.duration_max_ms > step.duration_ms:
            self._random_check.setChecked(True)
            self._max_spin.setValue(step.duration_max_ms)
        else:
            self._random_check.setChecked(False)
        self.update_description()
