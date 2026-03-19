"""Set Variable block."""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QLineEdit

from app.core.models import SetVariableStep
from app.ui.block_editor.blocks.base_block import BaseBlock, form_row, style_input


class VariableBlock(BaseBlock):
    HEADER_COLOR = "#FFD6E8"
    ICON = "📌"
    TYPE_LABEL = "SET VAR"

    def _build_body(self, layout: QVBoxLayout) -> None:
        self._name_edit = style_input(QLineEdit())
        self._name_edit.setPlaceholderText("variable_name")
        layout.addLayout(form_row("Name", self._name_edit))

        self._value_edit = style_input(QLineEdit())
        self._value_edit.setPlaceholderText("value  (supports {other_var})")
        layout.addLayout(form_row("Value", self._value_edit))

        self._name_edit.textChanged.connect(self._emit_changed)
        self._value_edit.textChanged.connect(self._emit_changed)

    def _emit_changed(self) -> None:
        self.update_description()
        self.changed.emit()

    def get_description(self) -> str:
        if not hasattr(self, "_name_edit"):
            return ""
        name = self._name_edit.text() or "?"
        val = self._value_edit.text()
        return f"{name} = '{val[:22]}'" if val else name

    def to_step(self) -> SetVariableStep:
        return SetVariableStep(
            name=self._name_edit.text(),
            value=self._value_edit.text(),
        )

    def from_step(self, step: SetVariableStep) -> None:
        self._name_edit.setText(step.name)
        self._value_edit.setText(step.value)
        self.update_description()
