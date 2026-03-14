"""
Condition evaluators.
Each evaluator polls until the condition is satisfied or times out.
"""
from __future__ import annotations
import time

from app.core.models import ConditionStep, ConditionType
from app.platform.screen_capture import get_pixel_color, color_matches


class ConditionTimeoutError(Exception):
    pass


def evaluate_condition(step: ConditionStep) -> bool:
    """
    Block until condition is satisfied or timeout is reached.
    Returns True if satisfied, raises ConditionTimeoutError otherwise.
    """
    if step.condition_type == ConditionType.PIXEL_COLOR:
        return _wait_pixel_color(step)
    raise NotImplementedError(f"Unsupported condition type: {step.condition_type}")


def _wait_pixel_color(step: ConditionStep) -> bool:
    deadline = time.monotonic() + step.timeout_ms / 1000.0
    interval = step.poll_interval_ms / 1000.0

    while time.monotonic() < deadline:
        actual = get_pixel_color(step.x, step.y)
        if color_matches(actual, step.expected_color, step.tolerance):
            return True
        time.sleep(interval)

    raise ConditionTimeoutError(
        f"Pixel at ({step.x}, {step.y}) did not match "
        f"{step.expected_color} within {step.timeout_ms} ms"
    )
