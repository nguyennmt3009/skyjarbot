"""
RunTracker: collects step-level telemetry during a scenario run
and persists the result to the database when the run finishes.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from app.core.models import Step, ActionStep, ConditionStep, DelayStep, ActionType, ConditionType
from app.data.run_models import RunRecord, StepRecord
from app.data.repository import save_run
from app.core.logger_service import get_logger

logger = get_logger(__name__)


class RunTracker:
    def __init__(self) -> None:
        self._run: Optional[RunRecord] = None
        self._current_step: Optional[StepRecord] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, scenario_id: str, scenario_name: str, total_steps: int) -> None:
        self._run = RunRecord(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            started_at=datetime.now(),
            total_steps=total_steps,
        )
        self._current_step = None

    def on_step_start(self, index: int, step: Step) -> None:
        if not self._run:
            return
        self._current_step = StepRecord(
            step_index=index,
            step_type=_step_type(step),
            description=_describe(step),
            started_at=datetime.now(),
        )

    def on_step_done(self, index: int, step: Step) -> None:
        if not self._run or not self._current_step:
            return
        self._current_step.finished_at = datetime.now()
        self._current_step.success = True
        self._run.steps.append(self._current_step)
        self._run.steps_done += 1
        self._current_step = None

    def on_step_error(self, index: int, step: Step, error: str) -> None:
        if not self._run:
            return
        if self._current_step is None:
            self._current_step = StepRecord(
                step_index=index,
                step_type=_step_type(step),
                description=_describe(step),
                started_at=datetime.now(),
            )
        self._current_step.finished_at = datetime.now()
        self._current_step.success = False
        self._current_step.error_msg = error
        self._run.steps.append(self._current_step)
        self._current_step = None

    def finish(self, success: bool) -> None:
        if not self._run:
            return
        self._run.finished_at = datetime.now()
        self._run.success = success
        try:
            save_run(self._run)
            logger.info("Run saved: scenario='%s' success=%s", self._run.scenario_name, success)
        except Exception as e:
            logger.error("Failed to save run record: %s", e)
        self._run = None
        self._current_step = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _step_type(step: Step) -> str:
    if isinstance(step, ActionStep):
        return step.action_type.value
    if isinstance(step, ConditionStep):
        return step.condition_type.value
    if isinstance(step, DelayStep):
        return "delay"
    return "unknown"


def _describe(step: Step) -> str:
    if isinstance(step, DelayStep):
        return f"delay {step.duration_ms} ms"
    if isinstance(step, ActionStep):
        t = step.action_type
        if t == ActionType.MOUSE_CLICK:
            return f"click ({step.x}, {step.y}) [{step.button}]"
        if t == ActionType.MOUSE_MOVE:
            return f"move ({step.x}, {step.y})"
        if t == ActionType.MOUSE_SCROLL:
            return f"scroll ({step.x}, {step.y})"
        if t == ActionType.KEY_PRESS:
            return f"key_press [{step.key}]"
        if t == ActionType.TYPE_TEXT:
            return f"type '{step.text}'"
    if isinstance(step, ConditionStep):
        ct = step.condition_type
        if ct == ConditionType.PIXEL_COLOR:
            return f"pixel ({step.x},{step.y}) == {step.expected_color}"
        if ct == ConditionType.IMAGE_MATCH:
            return f"image_match '{step.template_path}'"
        if ct == ConditionType.OCR_TEXT:
            return f"ocr_text '{step.expected_text}'"
    return repr(step)
