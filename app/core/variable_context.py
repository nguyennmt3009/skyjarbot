"""
VariableContext: a key-value store passed through scenario execution.
Supports {var_name} substitution in string fields.
"""
from __future__ import annotations
import re


class VariableContext:
    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self._vars: dict[str, str] = dict(initial or {})

    def set(self, name: str, value: str) -> None:
        self._vars[name] = value

    def get(self, name: str, default: str = "") -> str:
        return self._vars.get(name, default)

    def resolve(self, template: str) -> str:
        """Replace {var_name} placeholders with stored values."""
        if not template or "{" not in template:
            return template
        return re.sub(r"\{(\w+)\}", lambda m: self._vars.get(m.group(1), m.group(0)), template)

    def as_dict(self) -> dict[str, str]:
        return dict(self._vars)

    def __repr__(self) -> str:
        return f"VariableContext({self._vars!r})"
