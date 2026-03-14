"""
Player: replays a list of Steps sequentially in a background thread.
"""
from __future__ import annotations
import time
import threading
from typing import List, Callable, Optional

from app.core.models import ActionStep, ConditionStep, DelayStep, Step
from app.core.actions import execute_action
from app.core.conditions import evaluate_condition, ConditionTimeoutError
from app.core.logger_service import get_logger

logger = get_logger(__name__)


class Player:
    def __init__(
        self,
        on_step_start: Optional[Callable[[int, Step], None]] = None,
        on_step_done: Optional[Callable[[int, Step], None]] = None,
        on_step_error: Optional[Callable[[int, Step, str], None]] = None,
        on_finished: Optional[Callable[[bool], None]] = None,
    ):
        self._on_step_start = on_step_start
        self._on_step_done = on_step_done
        self._on_step_error = on_step_error
        self._on_finished = on_finished
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def play(self, steps: List[Step]) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, args=(steps,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self, steps: List[Step]) -> None:
        success = True
        for i, step in enumerate(steps):
            if self._stop_event.is_set():
                logger.info("Playback stopped by user at step %d", i)
                success = False
                break

            if self._on_step_start:
                self._on_step_start(i, step)

            try:
                if isinstance(step, ActionStep):
                    logger.debug("Executing action step %d: %s", i, step.action_type)
                    execute_action(step)
                elif isinstance(step, ConditionStep):
                    logger.debug("Evaluating condition step %d: %s", i, step.condition_type)
                    evaluate_condition(step)
                elif isinstance(step, DelayStep):
                    logger.debug("Delay step %d: %d ms", i, step.duration_ms)
                    self._interruptible_sleep(step.duration_ms / 1000.0)
            except ConditionTimeoutError as e:
                logger.error("Condition timeout at step %d: %s", i, e)
                if self._on_step_error:
                    self._on_step_error(i, step, str(e))
                success = False
                break
            except Exception as e:
                logger.error("Error at step %d: %s", i, e)
                if self._on_step_error:
                    self._on_step_error(i, step, str(e))
                success = False
                break

            if self._on_step_done:
                self._on_step_done(i, step)

        if self._on_finished:
            self._on_finished(success)

    def _interruptible_sleep(self, duration: float) -> None:
        end = time.monotonic() + duration
        while time.monotonic() < end:
            if self._stop_event.is_set():
                break
            time.sleep(0.05)
