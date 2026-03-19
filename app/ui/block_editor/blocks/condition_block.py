"""Condition block: wait for pixel, image match, or OCR text."""
from __future__ import annotations
from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QVBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QWidget, QCheckBox, QHBoxLayout, QLabel,
)

from app.core.models import ConditionStep, ConditionType
from app.ui.block_editor.blocks.base_block import (
    BaseBlock, form_row, style_input, pick_btn,
)


class ConditionBlock(BaseBlock):
    HEADER_COLOR = "#FFE8CC"
    ICON = "👁"
    TYPE_LABEL = "WAIT"

    def _build_body(self, layout: QVBoxLayout) -> None:
        self._type_combo = style_input(QComboBox())
        self._type_combo.addItems(["pixel_color", "image_match", "ocr_text"])
        layout.addLayout(form_row("Type", self._type_combo))

        self._timeout_spin = style_input(QSpinBox())
        self._timeout_spin.setRange(0, 60_000)
        self._timeout_spin.setValue(5000)
        self._timeout_spin.setSuffix(" ms")
        layout.addLayout(form_row("Timeout", self._timeout_spin))

        # ── pixel_color panel ─────────────────────────────────────────────────
        self._pixel_panel = QWidget()
        pp = QVBoxLayout(self._pixel_panel)
        pp.setContentsMargins(0, 0, 0, 0)
        pp.setSpacing(4)

        xy_row = QHBoxLayout()
        xy_row.setSpacing(4)
        lbl_xy = QLabel("X / Y")
        lbl_xy.setFixedWidth(70)
        lbl_xy.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        xy_row.addWidget(lbl_xy)
        self._px_x = style_input(QSpinBox())
        self._px_x.setRange(0, 9999)
        self._px_x.setFixedWidth(65)
        xy_row.addWidget(self._px_x)
        self._px_y = style_input(QSpinBox())
        self._px_y.setRange(0, 9999)
        self._px_y.setFixedWidth(65)
        xy_row.addWidget(self._px_y)
        self._px_pick = pick_btn()
        self._px_pick.clicked.connect(self._pick_pixel)
        xy_row.addWidget(self._px_pick)
        xy_row.addStretch()
        pp.addLayout(xy_row)

        rgb_row = QHBoxLayout()
        rgb_row.setSpacing(4)
        lbl_rgb = QLabel("R / G / B")
        lbl_rgb.setFixedWidth(70)
        lbl_rgb.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        rgb_row.addWidget(lbl_rgb)
        self._r_spin = style_input(QSpinBox())
        self._r_spin.setRange(0, 255)
        self._r_spin.setFixedWidth(55)
        rgb_row.addWidget(self._r_spin)
        self._g_spin = style_input(QSpinBox())
        self._g_spin.setRange(0, 255)
        self._g_spin.setFixedWidth(55)
        rgb_row.addWidget(self._g_spin)
        self._b_spin = style_input(QSpinBox())
        self._b_spin.setRange(0, 255)
        self._b_spin.setFixedWidth(55)
        rgb_row.addWidget(self._b_spin)
        rgb_row.addStretch()
        pp.addLayout(rgb_row)

        self._tol_spin = style_input(QSpinBox())
        self._tol_spin.setRange(0, 128)
        self._tol_spin.setValue(10)
        pp.addLayout(form_row("Tolerance", self._tol_spin))
        layout.addWidget(self._pixel_panel)

        # ── image_match panel ─────────────────────────────────────────────────
        self._img_panel = QWidget()
        ip = QVBoxLayout(self._img_panel)
        ip.setContentsMargins(0, 0, 0, 0)
        ip.setSpacing(4)

        img_path_row = QHBoxLayout()
        img_path_row.setSpacing(4)
        lbl_tp = QLabel("Template")
        lbl_tp.setFixedWidth(70)
        lbl_tp.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        img_path_row.addWidget(lbl_tp)
        self._template_edit = style_input(QLineEdit())
        self._template_edit.setPlaceholderText("path/to/template.png")
        img_path_row.addWidget(self._template_edit)
        from PySide6.QtWidgets import QPushButton
        browse_btn = QPushButton("📂")
        browse_btn.setFixedSize(26, 26)
        browse_btn.setStyleSheet("background:#EEF6FF; border:1px solid #C9DEF6; border-radius:5px;")
        browse_btn.clicked.connect(self._browse_template)
        img_path_row.addWidget(browse_btn)
        ip.addLayout(img_path_row)

        self._thresh_spin = style_input(QDoubleSpinBox())
        self._thresh_spin.setRange(0.0, 1.0)
        self._thresh_spin.setSingleStep(0.05)
        self._thresh_spin.setValue(0.8)
        ip.addLayout(form_row("Threshold", self._thresh_spin))

        self._region_edit = style_input(QLineEdit())
        self._region_edit.setPlaceholderText("x,y,w,h  (optional)")
        region_row = QHBoxLayout()
        region_row.setSpacing(4)
        region_lbl = QLabel("Region")
        region_lbl.setFixedWidth(70)
        region_lbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        region_row.addWidget(region_lbl)
        region_row.addWidget(self._region_edit)
        img_pick = pick_btn()
        img_pick.clicked.connect(self._pick_region_img)
        region_row.addWidget(img_pick)
        ip.addLayout(region_row)
        layout.addWidget(self._img_panel)

        # ── ocr panel ─────────────────────────────────────────────────────────
        self._ocr_panel = QWidget()
        op = QVBoxLayout(self._ocr_panel)
        op.setContentsMargins(0, 0, 0, 0)
        op.setSpacing(4)

        self._ocr_text_edit = style_input(QLineEdit())
        self._ocr_text_edit.setPlaceholderText("Expected text…")
        op.addLayout(form_row("Text", self._ocr_text_edit))

        self._ocr_contains = QCheckBox("Substring match (contains)")
        self._ocr_contains.setChecked(True)
        self._ocr_contains.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.6);")
        op.addWidget(self._ocr_contains)

        self._ocr_region_edit = style_input(QLineEdit())
        self._ocr_region_edit.setPlaceholderText("x,y,w,h  (optional)")
        ocr_region_row = QHBoxLayout()
        ocr_region_row.setSpacing(4)
        ocr_rlbl = QLabel("Region")
        ocr_rlbl.setFixedWidth(70)
        ocr_rlbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        ocr_region_row.addWidget(ocr_rlbl)
        ocr_region_row.addWidget(self._ocr_region_edit)
        ocr_pick = pick_btn()
        ocr_pick.clicked.connect(self._pick_region_ocr)
        ocr_region_row.addWidget(ocr_pick)
        op.addLayout(ocr_region_row)
        layout.addWidget(self._ocr_panel)

        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed("pixel_color")

        for sp in (self._px_x, self._px_y, self._r_spin, self._g_spin, self._b_spin, self._tol_spin):
            sp.valueChanged.connect(self._emit_changed)
        self._template_edit.textChanged.connect(self._emit_changed)
        self._ocr_text_edit.textChanged.connect(self._emit_changed)

    def _on_type_changed(self, t: str) -> None:
        self._pixel_panel.setVisible(t == "pixel_color")
        self._img_panel.setVisible(t == "image_match")
        self._ocr_panel.setVisible(t == "ocr_text")
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
            # sample color from screen
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                r, g, b = img.getpixel((x, y))[:3]
                self._r_spin.setValue(r)
                self._g_spin.setValue(g)
                self._b_spin.setValue(b)
            except Exception:
                pass

    def _pick_region_img(self) -> None:
        from app.ui.screen_picker_qt import ScreenPickerQt
        picker = ScreenPickerQt(mode="region")
        if picker.exec() and picker.result_region:
            self._region_edit.setText(",".join(str(v) for v in picker.result_region))

    def _pick_region_ocr(self) -> None:
        from app.ui.screen_picker_qt import ScreenPickerQt
        picker = ScreenPickerQt(mode="region")
        if picker.exec() and picker.result_region:
            self._ocr_region_edit.setText(",".join(str(v) for v in picker.result_region))

    def _browse_template(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select Template", "",
                                               "Images (*.png *.jpg *.bmp)")
        if path:
            self._template_edit.setText(path)

    def get_description(self) -> str:
        if not hasattr(self, "_type_combo"):
            return ""
        t = self._type_combo.currentText()
        if t == "pixel_color":
            return (f"pixel ({self._px_x.value()},{self._px_y.value()}) = "
                    f"({self._r_spin.value()},{self._g_spin.value()},{self._b_spin.value()}) "
                    f"±{self._tol_spin.value()}")
        if t == "image_match":
            import os
            name = os.path.basename(self._template_edit.text()) or "?"
            return f"image '{name}' ≥ {self._thresh_spin.value():.2f}"
        if t == "ocr_text":
            txt = self._ocr_text_edit.text()
            mode = "contains" if self._ocr_contains.isChecked() else "exact"
            return f"ocr '{txt[:20]}' [{mode}]"
        return ""

    def to_step(self) -> ConditionStep:
        t = self._type_combo.currentText()
        ct = ConditionType(t)
        step = ConditionStep(
            condition_type=ct,
            timeout_ms=self._timeout_spin.value(),
        )
        if ct == ConditionType.PIXEL_COLOR:
            step.x = self._px_x.value()
            step.y = self._px_y.value()
            step.expected_color = (self._r_spin.value(), self._g_spin.value(), self._b_spin.value())
            step.tolerance = self._tol_spin.value()
        elif ct == ConditionType.IMAGE_MATCH:
            step.template_path = self._template_edit.text()
            step.match_threshold = self._thresh_spin.value()
            step.search_region = _parse_region(self._region_edit.text())
        elif ct == ConditionType.OCR_TEXT:
            step.expected_text = self._ocr_text_edit.text()
            step.ocr_contains = self._ocr_contains.isChecked()
            step.ocr_region = _parse_region(self._ocr_region_edit.text())
        return step

    def from_step(self, step: ConditionStep) -> None:
        self._type_combo.setCurrentText(step.condition_type.value)
        self._timeout_spin.setValue(step.timeout_ms)
        if step.condition_type == ConditionType.PIXEL_COLOR:
            self._px_x.setValue(step.x)
            self._px_y.setValue(step.y)
            self._r_spin.setValue(step.expected_color[0])
            self._g_spin.setValue(step.expected_color[1])
            self._b_spin.setValue(step.expected_color[2])
            self._tol_spin.setValue(step.tolerance)
        elif step.condition_type == ConditionType.IMAGE_MATCH:
            self._template_edit.setText(step.template_path)
            self._thresh_spin.setValue(step.match_threshold)
            if step.search_region:
                self._region_edit.setText(",".join(str(v) for v in step.search_region))
        elif step.condition_type == ConditionType.OCR_TEXT:
            self._ocr_text_edit.setText(step.expected_text)
            self._ocr_contains.setChecked(step.ocr_contains)
            if step.ocr_region:
                self._ocr_region_edit.setText(",".join(str(v) for v in step.ocr_region))
        self.update_description()


def _parse_region(text: str):
    try:
        parts = [int(v.strip()) for v in text.split(",")]
        if len(parts) == 4:
            return tuple(parts)
    except (ValueError, AttributeError):
        pass
    return None
