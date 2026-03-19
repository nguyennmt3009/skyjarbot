"""
Scenario serialization: JSON <-> Scenario dataclass.
"""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import Union

from app.core.models import (
    Scenario, ActionStep, ConditionStep, DelayStep,
    BranchStep, LoopStep, SetVariableStep, CallScenarioStep,
    Step, ActionType, ConditionType, StepType,
)


# ── Serialize ────────────────────────────────────────────────────────────────

def scenario_to_dict(scenario: Scenario) -> dict:
    return {
        "id": scenario.id or str(uuid.uuid4()),
        "name": scenario.name,
        "description": scenario.description,
        "version": scenario.version,
        "steps": [_step_to_dict(s) for s in scenario.steps],
    }


def _step_to_dict(step: Step) -> dict:
    if isinstance(step, ActionStep):
        d = {"type": step.action_type.value}
        if step.x is not None:
            d["x"] = step.x
        if step.y is not None:
            d["y"] = step.y
        if step.action_type == ActionType.MOUSE_CLICK:
            d["button"] = step.button
        elif step.action_type == ActionType.KEY_PRESS and step.key:
            d["key"] = step.key
        elif step.action_type == ActionType.TYPE_TEXT and step.text:
            d["text"] = step.text
        elif step.action_type == ActionType.MOUSE_SCROLL:
            d["dx"] = step.dx
            d["dy"] = step.dy
        return d

    if isinstance(step, ConditionStep):
        base = {
            "type": step.condition_type.value,
            "timeout_ms": step.timeout_ms,
            "poll_interval_ms": step.poll_interval_ms,
        }
        if step.condition_type == ConditionType.PIXEL_COLOR:
            base.update({
                "x": step.x,
                "y": step.y,
                "color": list(step.expected_color),
                "tolerance": step.tolerance,
            })
        elif step.condition_type == ConditionType.IMAGE_MATCH:
            base.update({
                "template_path": step.template_path,
                "match_threshold": step.match_threshold,
                "search_region": list(step.search_region) if step.search_region else None,
            })
        elif step.condition_type == ConditionType.OCR_TEXT:
            base.update({
                "expected_text": step.expected_text,
                "ocr_contains": step.ocr_contains,
                "ocr_region": list(step.ocr_region) if step.ocr_region else None,
            })
        return base

    if isinstance(step, DelayStep):
        d = {"type": "delay", "duration_ms": step.duration_ms}
        if step.duration_max_ms is not None:
            d["duration_max_ms"] = step.duration_max_ms
        return d

    if isinstance(step, BranchStep):
        return {
            "type": "branch",
            "condition": _step_to_dict(step.condition),
            "on_true":  [_step_to_dict(s) for s in step.on_true],
            "on_false": [_step_to_dict(s) for s in step.on_false],
        }

    if isinstance(step, LoopStep):
        return {
            "type": "loop",
            "count": step.count,
            "body": [_step_to_dict(s) for s in step.body],
        }

    if isinstance(step, SetVariableStep):
        return {"type": "set_variable", "name": step.name, "value": step.value}

    if isinstance(step, CallScenarioStep):
        return {"type": "call_scenario", "scenario_path": step.scenario_path}

    raise ValueError(f"Unknown step type: {type(step)}")


# ── Deserialize ───────────────────────────────────────────────────────────────

_ACTION_TYPES = {a.value for a in ActionType}
_CONDITION_TYPES = {c.value for c in ConditionType}


def dict_to_scenario(data: dict) -> Scenario:
    steps = [_dict_to_step(s) for s in data.get("steps", [])]
    return Scenario(
        id=data.get("id", ""),
        name=data.get("name", ""),
        description=data.get("description", ""),
        version=data.get("version", 1),
        steps=steps,
    )


def _dict_to_step(data: dict) -> Step:
    t = data["type"]

    if t in _ACTION_TYPES:
        step = ActionStep(action_type=ActionType(t))
        step.x = data.get("x")
        step.y = data.get("y")
        step.button = data.get("button", "left")
        step.key = data.get("key")
        step.text = data.get("text")
        step.dx = data.get("dx", 0)
        step.dy = data.get("dy", 0)
        return step

    if t in _CONDITION_TYPES:
        ct = ConditionType(t)
        common = dict(
            condition_type=ct,
            timeout_ms=data.get("timeout_ms", 5000),
            poll_interval_ms=data.get("poll_interval_ms", 200),
        )
        if ct == ConditionType.PIXEL_COLOR:
            color = tuple(data.get("color", [0, 0, 0]))
            return ConditionStep(
                **common,
                x=data.get("x", 0),
                y=data.get("y", 0),
                expected_color=color,
                tolerance=data.get("tolerance", 10),
            )
        if ct == ConditionType.IMAGE_MATCH:
            sr = data.get("search_region")
            return ConditionStep(
                **common,
                template_path=data.get("template_path", ""),
                match_threshold=data.get("match_threshold", 0.8),
                search_region=tuple(sr) if sr else None,
            )
        if ct == ConditionType.OCR_TEXT:
            ocr_r = data.get("ocr_region")
            return ConditionStep(
                **common,
                expected_text=data.get("expected_text", ""),
                ocr_contains=data.get("ocr_contains", True),
                ocr_region=tuple(ocr_r) if ocr_r else None,
            )

    if t == "delay":
        step = DelayStep(duration_ms=data.get("duration_ms", 1000))
        step.duration_max_ms = data.get("duration_max_ms")
        return step

    if t == "branch":
        condition = _dict_to_step(data["condition"])
        return BranchStep(
            condition=condition,
            on_true=[_dict_to_step(s) for s in data.get("on_true", [])],
            on_false=[_dict_to_step(s) for s in data.get("on_false", [])],
        )

    if t == "loop":
        return LoopStep(
            count=data.get("count", 1),
            body=[_dict_to_step(s) for s in data.get("body", [])],
        )

    if t == "set_variable":
        return SetVariableStep(name=data.get("name", ""), value=data.get("value", ""))

    if t == "call_scenario":
        return CallScenarioStep(scenario_path=data.get("scenario_path", ""))

    raise ValueError(f"Unknown step type in JSON: {t!r}")


# ── File I/O ──────────────────────────────────────────────────────────────────

def save_scenario(scenario: Scenario, path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scenario_to_dict(scenario), f, indent=2, ensure_ascii=False)


def load_scenario(path: Union[str, Path]) -> Scenario:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_scenario(data)
