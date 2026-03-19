"""Action block: click, key_press, type_text, mouse_move, mouse_scroll."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QLineEdit,
    QWidget, QLabel,
)
from PySide6.QtCore import Qt

from app.core.models import ActionStep, ActionType
from app.ui.block_editor.blocks.base_block import (
    BaseBlock, form_row, style_input, pick_btn,
)

_ACTION_LABELS = {
    "click":       ("🖱", "CLICK",  "#D0E8FF", "#64B5F6"),
    "mouse_move":  ("↔", "MOVE",   "#D0E8FF", "#64B5F6"),
    "mouse_scroll":("↕", "SCROLL", "#D0E8FF", "#64B5F6"),
    "key_press":   ("⌨", "KEY",    "#DCF0FF", "#5BA8E0"),
    "type_text":   ("📝","TYPE",   "#DCF0FF", "#5BA8E0"),
}


class ActionBlock(BaseBlock):
    HEADER_COLOR = "#D0E8FF"
    ICON = "🖱"
    TYPE_LABEL = "ACTION"

    def __init__(self, action_type: str = "click", parent=None):
        self._init_action_type = action_type
        super().__init__(parent)
        self._apply_type_style(action_type)

    # ── Body ──────────────────────────────────────────────────────────────────

    def _build_body(self, layout: QVBoxLayout) -> None:
        # Action type selector
        self._type_combo = style_input(QComboBox())
        self._type_combo.addItems([
            "click", "mouse_move", "mouse_scroll", "key_press", "type_text"
        ])
        self._type_combo.setCurrentText(self._init_action_type)
        layout.addLayout(form_row("Type", self._type_combo))
        self._type_combo.currentTextChanged.connect(self._on_type_changed)

        # X / Y + picker
        xy_row = QHBoxLayout()
        xy_row.setSpacing(4)
        lbl = QLabel("X / Y")
        lbl.setFixedWidth(70)
        lbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        xy_row.addWidget(lbl)
        self._x_spin = style_input(QSpinBox())
        self._x_spin.setRange(0, 9999)
        self._x_spin.setFixedWidth(70)
        xy_row.addWidget(self._x_spin)
        self._y_spin = style_input(QSpinBox())
        self._y_spin.setRange(0, 9999)
        self._y_spin.setFixedWidth(70)
        xy_row.addWidget(self._y_spin)
        self._pick_btn = pick_btn()
        self._pick_btn.clicked.connect(self._pick_point)
        xy_row.addWidget(self._pick_btn)
        xy_row.addStretch()
        self._xy_widget = QWidget()
        self._xy_widget.setLayout(xy_row)
        layout.addWidget(self._xy_widget)

        # Button (click)
        self._btn_combo = style_input(QComboBox())
        self._btn_combo.addItems(["left", "right", "middle"])
        self._btn_row_widget = QWidget()
        self._btn_row_widget.setLayout(form_row("Button", self._btn_combo))
        layout.addWidget(self._btn_row_widget)

        # Scroll dx/dy
        scroll_row = QHBoxLayout()
        scroll_row.setSpacing(4)
        slbl = QLabel("dx / dy")
        slbl.setFixedWidth(70)
        slbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
        scroll_row.addWidget(slbl)
        self._dx_spin = style_input(QSpinBox())
        self._dx_spin.setRange(-999, 999)
        self._dx_spin.setFixedWidth(70)
        scroll_row.addWidget(self._dx_spin)
        self._dy_spin = style_input(QSpinBox())
        self._dy_spin.setRange(-999, 999)
        self._dy_spin.setFixedWidth(70)
        scroll_row.addWidget(self._dy_spin)
        scroll_row.addStretch()
        self._scroll_widget = QWidget()
        self._scroll_widget.setLayout(scroll_row)
        layout.addWidget(self._scroll_widget)

        # Key
        self._key_edit = style_input(QLineEdit())
        self._key_edit.setPlaceholderText("e.g. Key.enter, a, F5")
        self._key_widget = QWidget()
        self._key_widget.setLayout(form_row("Key", self._key_edit))
        layout.addWidget(self._key_widget)

        # Text
        self._text_edit = style_input(QLineEdit())
        self._text_edit.setPlaceholderText("Text to type…")
        self._text_widget = QWidget()
        self._text_widget.setLayout(form_row("Text", self._text_edit))
        layout.addWidget(self._text_widget)

        # Connect all fields to description update
        for w in (self._x_spin, self._y_spin, self._dx_spin, self._dy_spin):
            w.valueChanged.connect(self._emit_changed)
        for w in (self._key_edit, self._text_edit):
            w.textChanged.connect(self._emit_changed)
        self._btn_combo.currentTextChanged.connect(self._emit_changed)

        self._on_type_changed(self._init_action_type)

    def _on_type_changed(self, t: str) -> None:
        use_xy     = t in ("click", "mouse_move", "mouse_scroll")
        use_btn    = t == "click"
        use_scroll = t == "mouse_scroll"
        use_key    = t == "key_press"
        use_text   = t == "type_text"

        self._xy_widget.setVisible(use_xy)
        self._pick_btn.setVisible(use_xy)
        self._btn_row_widget.setVisible(use_btn)
        self._scroll_widget.setVisible(use_scroll)
        self._key_widget.setVisible(use_key)
        self._text_widget.setVisible(use_text)
        self._apply_type_style(t)
        self._emit_changed()

    def _apply_type_style(self, t: str) -> None:
        icon, label, color, _ = _ACTION_LABELS.get(t, ("🖱", "ACTION", "#D0E8FF", "#64B5F6"))
        self.HEADER_COLOR = color
        self.ICON = icon
        self.TYPE_LABEL = label
        if hasattr(self, "_header"):
            self._header._icon_lbl.setText(icon)
            self._header._bg = color
            self._header._apply_style(False)

    def _emit_changed(self) -> None:
        self.update_description()
        self.changed.emit()

    def _pick_point(self) -> None:
        from app.ui.screen_picker_qt import ScreenPickerQt
        picker = ScreenPickerQt(mode="point")
        if picker.exec() and picker.result_point:
            self._x_spin.setValue(picker.result_point[0])
            self._y_spin.setValue(picker.result_point[1])

    # ── Step conversion ───────────────────────────────────────────────────────

    def get_description(self) -> str:
        t = self._type_combo.currentText() if hasattr(self, "_type_combo") else ""
        if t == "click":
            return f"({self._x_spin.value()}, {self._y_spin.value()})  {self._btn_combo.currentText()}"
        if t == "mouse_move":
            return f"({self._x_spin.value()}, {self._y_spin.value()})"
        if t == "mouse_scroll":
            return f"({self._x_spin.value()}, {self._y_spin.value()})  dx={self._dx_spin.value()} dy={self._dy_spin.value()}"
        if t == "key_press":
            return self._key_edit.text() or "(key)"
        if t == "type_text":
            txt = self._text_edit.text()
            return f"'{txt[:24]}'" if txt else "(text)"
        return ""

    def to_step(self) -> ActionStep:
        t = self._type_combo.currentText()
        step = ActionStep(action_type=ActionType(t))
        step.x = self._x_spin.value()
        step.y = self._y_spin.value()
        step.button = self._btn_combo.currentText()
        step.key = self._key_edit.text() or None
        step.text = self._text_edit.text() or None
        step.dx = self._dx_spin.value()
        step.dy = self._dy_spin.value()
        return step

    def from_step(self, step: ActionStep) -> None:
        t = step.action_type.value
        self._type_combo.setCurrentText(t)
        self._x_spin.setValue(step.x or 0)
        self._y_spin.setValue(step.y or 0)
        self._btn_combo.setCurrentText(step.button or "left")
        self._key_edit.setText(step.key or "")
        self._text_edit.setText(step.text or "")
        self._dx_spin.setValue(step.dx)
        self._dy_spin.setValue(step.dy)
        self.update_description()
