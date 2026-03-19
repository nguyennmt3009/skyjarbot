"""Branch block: IF condition → THEN steps / ELSE steps."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QComboBox, QSpinBox, QLabel, QWidget, QHBoxLayout,
)
from PySide6.QtCore import Qt

from app.core.models import BranchStep, ConditionStep, ConditionType
from app.ui.block_editor.blocks.base_block import BaseBlock, form_row, style_input, pick_btn


class BranchBlock(BaseBlock):
    HEADER_COLOR = "#D5EFDD"
    ICON = "⬦"
    TYPE_LABEL = "IF / ELSE"

    def _build_body(self, layout: QVBoxLayout) -> None:
        # ── Condition mini-form ───────────────────────────────────────────────
        self._cond_type = style_input(QComboBox())
        self._cond_type.addItems(["pixel_color", "image_match", "ocr_text"])
        layout.addLayout(form_row("Condition", self._cond_type))

        # Pixel color
        self._px_panel = QWidget()
        pp = QVBoxLayout(self._px_panel)
        pp.setContentsMargins(0, 0, 0, 0)
        pp.setSpacing(4)

        xy_row = QHBoxLayout()
        xy_row.setSpacing(4)
        lbl = QLabel("X / Y")
        lbl.setFixedWidth(70)
        lbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        xy_row.addWidget(lbl)
        self._px_x = style_input(QSpinBox()); self._px_x.setRange(0, 9999); self._px_x.setFixedWidth(65)
        self._px_y = style_input(QSpinBox()); self._px_y.setRange(0, 9999); self._px_y.setFixedWidth(65)
        xy_row.addWidget(self._px_x)
        xy_row.addWidget(self._px_y)
        self._px_pick = pick_btn()
        self._px_pick.clicked.connect(self._pick_pixel)
        xy_row.addWidget(self._px_pick)
        xy_row.addStretch()
        pp.addLayout(xy_row)

        rgb_row = QHBoxLayout()
        rgb_row.setSpacing(4)
        rl = QLabel("R / G / B"); rl.setFixedWidth(70)
        rl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        rgb_row.addWidget(rl)
        self._r = style_input(QSpinBox()); self._r.setRange(0, 255); self._r.setFixedWidth(55)
        self._g = style_input(QSpinBox()); self._g.setRange(0, 255); self._g.setFixedWidth(55)
        self._b = style_input(QSpinBox()); self._b.setRange(0, 255); self._b.setFixedWidth(55)
        rgb_row.addWidget(self._r); rgb_row.addWidget(self._g); rgb_row.addWidget(self._b)
        rgb_row.addStretch()
        pp.addLayout(rgb_row)

        self._tol = style_input(QSpinBox()); self._tol.setRange(0, 128); self._tol.setValue(10)
        pp.addLayout(form_row("Tolerance", self._tol))
        layout.addWidget(self._px_panel)

        self._timeout_spin = style_input(QSpinBox())
        self._timeout_spin.setRange(0, 60_000)
        self._timeout_spin.setValue(3000)
        self._timeout_spin.setSuffix(" ms")
        layout.addLayout(form_row("Timeout", self._timeout_spin))

        self._cond_type.currentTextChanged.connect(self._on_cond_changed)
        self._on_cond_changed("pixel_color")

        # ── THEN container ────────────────────────────────────────────────────
        layout.addWidget(_section_label("THEN", "#27AE60"))
        from app.ui.block_editor.block_canvas import BlockCanvas
        self._then_canvas = BlockCanvas(compact=True)
        layout.addWidget(self._then_canvas)
        self._then_canvas.blocks_changed.connect(self._emit_changed)

        # ── ELSE container ────────────────────────────────────────────────────
        layout.addWidget(_section_label("ELSE", "#E67E22"))
        self._else_canvas = BlockCanvas(compact=True)
        layout.addWidget(self._else_canvas)
        self._else_canvas.blocks_changed.connect(self._emit_changed)

        for w in (self._px_x, self._px_y, self._r, self._g, self._b, self._tol):
            w.valueChanged.connect(self._emit_changed)

    def _on_cond_changed(self, t: str) -> None:
        self._px_panel.setVisible(t == "pixel_color")
        self._emit_changed()

    def _emit_changed(self) -> None:
        self.update_description()
        self.changed.emit()

    def _pick_pixel(self) -> None:
        from app.ui.screen_picker_qt import ScreenPickerQt
        picker = ScreenPickerQt(mode="point")
        if picker.exec() and picker.result_point:
            x, y = picker.result_point
            self._px_x.setValue(x)
            self._px_y.setValue(y)
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                r, g, b = img.getpixel((x, y))[:3]
                self._r.setValue(r); self._g.setValue(g); self._b.setValue(b)
            except Exception:
                pass

    def get_description(self) -> str:
        if not hasattr(self, "_cond_type"):
            return ""
        t = self._cond_type.currentText()
        if t == "pixel_color":
            return (f"pixel ({self._px_x.value()},{self._px_y.value()}) = "
                    f"({self._r.value()},{self._g.value()},{self._b.value()})")
        return t

    def to_step(self) -> BranchStep:
        ct = ConditionType(self._cond_type.currentText())
        cond = ConditionStep(condition_type=ct, timeout_ms=self._timeout_spin.value())
        if ct == ConditionType.PIXEL_COLOR:
            cond.x = self._px_x.value()
            cond.y = self._px_y.value()
            cond.expected_color = (self._r.value(), self._g.value(), self._b.value())
            cond.tolerance = self._tol.value()
        return BranchStep(
            condition=cond,
            on_true=self._then_canvas.get_steps(),
            on_false=self._else_canvas.get_steps(),
        )

    def from_step(self, step: BranchStep) -> None:
        self._cond_type.setCurrentText(step.condition.condition_type.value)
        c = step.condition
        if c.condition_type == ConditionType.PIXEL_COLOR:
            self._px_x.setValue(c.x)
            self._px_y.setValue(c.y)
            self._r.setValue(c.expected_color[0])
            self._g.setValue(c.expected_color[1])
            self._b.setValue(c.expected_color[2])
            self._tol.setValue(c.tolerance)
        self._timeout_spin.setValue(c.timeout_ms)
        self._then_canvas.load_steps(step.on_true)
        self._else_canvas.load_steps(step.on_false)
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
