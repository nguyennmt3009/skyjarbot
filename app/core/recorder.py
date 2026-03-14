"""
Recorder: captures mouse/keyboard events and converts them into Steps.
"""
from __future__ import annotations
import time
from typing import List, Callable, Optional

from app.core.models import ActionStep, ActionType, DelayStep, Step
from app.platform.input_hooks import InputHooks


class Recorder:
    """
    Records user input and builds a list of Steps.
    A DelayStep is inserted between events to preserve timing.
    """

    def __init__(self, on_step_recorded: Optional[Callable[[Step], None]] = None):
        self._steps: List[Step] = []
        self._last_event_time: Optional[float] = None
        self._on_step_recorded = on_step_recorded
        self._hooks = InputHooks(
            on_mouse_click=self._handle_click,
            on_mouse_scroll=self._handle_scroll,
            on_key_press=self._handle_key_press,
        )
        self._recording = False

    @property
    def steps(self) -> List[Step]:
        return list(self._steps)

    def start(self) -> None:
        self._steps.clear()
        self._last_event_time = time.monotonic()
        self._recording = True
        self._hooks.start()

    def stop(self) -> None:
        self._recording = False
        self._hooks.stop()

    def _record(self, step: Step) -> None:
        now = time.monotonic()
        if self._last_event_time is not None:
            delay_ms = int((now - self._last_event_time) * 1000)
            if delay_ms > 50:
                delay = DelayStep(duration_ms=delay_ms)
                self._steps.append(delay)
                if self._on_step_recorded:
                    self._on_step_recorded(delay)
        self._last_event_time = now
        self._steps.append(step)
        if self._on_step_recorded:
            self._on_step_recorded(step)

    def _handle_click(self, x: int, y: int, button: str) -> None:
        if not self._recording:
            return
        step = ActionStep(action_type=ActionType.MOUSE_CLICK, x=x, y=y, button=button)
        self._record(step)

    def _handle_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._recording:
            return
        step = ActionStep(action_type=ActionType.MOUSE_SCROLL, x=x, y=y, dx=dx, dy=dy)
        self._record(step)

    def _handle_key_press(self, key: str) -> None:
        if not self._recording:
            return
        step = ActionStep(action_type=ActionType.KEY_PRESS, key=key)
        self._record(step)
