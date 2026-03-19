"""
Player: replays a list of Steps sequentially in a background thread.
Supports branching, variables, and nested/call scenarios.
"""
from __future__ import annotations
import time
import random
import threading
from typing import List, Callable, Optional

from app.core.models import (
    ActionStep, ConditionStep, DelayStep,
    BranchStep, LoopStep, SetVariableStep, CallScenarioStep,
    Step,
)
from app.core.actions import execute_action
from app.core.conditions import evaluate_condition, ConditionTimeoutError
from app.core.variable_context import VariableContext
from app.core.logger_service import get_logger

logger = get_logger(__name__)


class Player:
    def __init__(
        self,
        on_step_start: Optional[Callable[[int, Step], None]] = None,
        on_step_done:  Optional[Callable[[int, Step], None]] = None,
        on_step_error: Optional[Callable[[int, Step, str], None]] = None,
        on_finished:   Optional[Callable[[bool], None]] = None,
    ):
        self._on_step_start = on_step_start
        self._on_step_done  = on_step_done
        self._on_step_error = on_step_error
        self._on_finished   = on_finished
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._variables = VariableContext()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def play(self, steps: List[Step], variables: Optional[VariableContext] = None) -> None:
        if self.is_running:
            return
        self._variables = variables or VariableContext()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, args=(steps,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    # ── Top-level run ─────────────────────────────────────────────────────────

    def _run(self, steps: List[Step]) -> None:
        success = self._execute_steps(steps, top_level=True)
        if self._on_finished:
            self._on_finished(success)

    # ── Step list executor ────────────────────────────────────────────────────

    def _execute_steps(self, steps: List[Step], top_level: bool = False) -> bool:
        for i, step in enumerate(steps):
            if self._stop_event.is_set():
                logger.info("Playback stopped by user at step %d", i)
                return False

            if top_level and self._on_step_start:
                self._on_step_start(i, step)

            try:
                ok = self._execute_step(i, step)
            except Exception as e:
                msg = str(e)
                logger.error("Error at step %d: %s", i, msg)
                if top_level and self._on_step_error:
                    self._on_step_error(i, step, msg)
                return False

            if not ok:
                return False

            if top_level and self._on_step_done:
                self._on_step_done(i, step)

        return True

    # ── Single step executor ──────────────────────────────────────────────────

    def _execute_step(self, i: int, step: Step) -> bool:
        if isinstance(step, ActionStep):
            resolved = self._resolve_action(step)
            logger.debug("Action step %d: %s", i, resolved.action_type)
            execute_action(resolved)
            return True

        if isinstance(step, ConditionStep):
            logger.debug("Condition step %d: %s", i, step.condition_type)
            evaluate_condition(step)          # raises ConditionTimeoutError on failure
            return True

        if isinstance(step, DelayStep):
            if step.duration_max_ms is not None and step.duration_max_ms > step.duration_ms:
                actual_ms = random.randint(step.duration_ms, step.duration_max_ms)
            else:
                actual_ms = step.duration_ms
            logger.debug("Delay step %d: %d ms", i, actual_ms)
            self._interruptible_sleep(actual_ms / 1000.0)
            return True

        if isinstance(step, BranchStep):
            return self._execute_branch(i, step)

        if isinstance(step, LoopStep):
            return self._execute_loop(i, step)

        if isinstance(step, SetVariableStep):
            resolved_value = self._variables.resolve(step.value)
            self._variables.set(step.name, resolved_value)
            logger.info("Variable set: %s = %r", step.name, resolved_value)
            return True

        if isinstance(step, CallScenarioStep):
            return self._execute_call(i, step)

        logger.warning("Unknown step type at %d: %s", i, type(step))
        return True

    # ── Branch ────────────────────────────────────────────────────────────────

    def _execute_branch(self, i: int, step: BranchStep) -> bool:
        try:
            condition_met = evaluate_condition(step.condition)
        except ConditionTimeoutError:
            condition_met = False

        branch = step.on_true if condition_met else step.on_false
        label  = "on_true" if condition_met else "on_false"
        logger.info("Branch step %d: condition=%s → executing %s (%d steps)",
                    i, condition_met, label, len(branch))
        return self._execute_steps(branch, top_level=False)

    # ── Loop ──────────────────────────────────────────────────────────────────

    def _execute_loop(self, i: int, step: LoopStep) -> bool:
        target = step.count if step.count > 0 else None   # None = infinite
        iteration = 0
        logger.info("Loop step %d: count=%s body=%d steps", i, step.count or "∞", len(step.body))
        while (target is None or iteration < target) and not self._stop_event.is_set():
            ok = self._execute_steps(step.body, top_level=False)
            if not ok:
                return False
            iteration += 1
        return True

    # ── Call scenario ─────────────────────────────────────────────────────────

    def _execute_call(self, i: int, step: CallScenarioStep) -> bool:
        from app.core.serializer import load_scenario
        try:
            sub = load_scenario(step.scenario_path)
        except Exception as e:
            raise RuntimeError(f"CallScenario failed to load '{step.scenario_path}': {e}") from e
        logger.info("Call step %d: running sub-scenario '%s' (%d steps)",
                    i, sub.name, len(sub.steps))
        return self._execute_steps(sub.steps, top_level=False)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _resolve_action(self, step: ActionStep) -> ActionStep:
        """Return a copy of the step with {variables} substituted."""
        import copy
        s = copy.copy(step)
        if s.text:
            s.text = self._variables.resolve(s.text)
        if s.key:
            s.key = self._variables.resolve(s.key)
        return s

    def _interruptible_sleep(self, duration: float) -> None:
        end = time.monotonic() + duration
        while time.monotonic() < end:
            if self._stop_event.is_set():
                break
            time.sleep(0.05)
