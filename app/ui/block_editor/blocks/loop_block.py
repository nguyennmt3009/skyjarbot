"""Loop block: repeat body steps N times (0 = infinite)."""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QSpinBox, QLabel
from PySide6.QtCore import Qt

from app.core.models import LoopStep
from app.ui.block_editor.blocks.base_block import BaseBlock, form_row, style_input


class LoopBlock(BaseBlock):
    HEADER_COLOR = "#FFF5CC"
    ICON = "🔁"
    TYPE_LABEL = "LOOP"

    def _build_body(self, layout: QVBoxLayout) -> None:
        self._count_spin = style_input(QSpinBox())
        self._count_spin.setRange(0, 9999)
        self._count_spin.setValue(3)
        self._count_spin.setSpecialValueText("∞  (infinite)")
        self._count_spin.setToolTip("0 = repeat forever")
        layout.addLayout(form_row("Count", self._count_spin))

        layout.addWidget(_section_label("BODY", "#B8860B"))
        from app.ui.block_editor.block_canvas import BlockCanvas
        self._body_canvas = BlockCanvas(compact=True)
        layout.addWidget(self._body_canvas)

        self._count_spin.valueChanged.connect(self._emit_changed)
        self._body_canvas.blocks_changed.connect(self._emit_changed)

    def _emit_changed(self) -> None:
        self.update_description()
        self.changed.emit()

    def get_description(self) -> str:
        if not hasattr(self, "_count_spin"):
            return ""
        n = self._count_spin.value()
        count_str = "∞" if n == 0 else str(n)
        body_count = len(self._body_canvas.get_blocks()) if hasattr(self, "_body_canvas") else 0
        return f"{count_str} ×  ({body_count} step{'s' if body_count != 1 else ''})"

    def to_step(self) -> LoopStep:
        return LoopStep(
            count=self._count_spin.value(),
            body=self._body_canvas.get_steps(),
        )

    def from_step(self, step: LoopStep) -> None:
        self._count_spin.setValue(step.count)
        self._body_canvas.load_steps(step.body)
        self.update_description()


def _section_label(text: str, color: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        QLabel {{
            font-size: 10px;
            font-weight: 700;
            color: {color};
            letter-spacing: 1px;
            padding: 4px 0 1px 0;
        }}
    """)
    return lbl
