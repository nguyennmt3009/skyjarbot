"""
Scenario Engine: loads and executes a Scenario using Player.
High-level entry point for running automation scenarios.
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional

from app.core.models import Scenario, Step
from app.core.player import Player
from app.core.serializer import load_scenario
from app.core.run_tracker import RunTracker
from app.data.database import init_db
from app.core.logger_service import get_logger

logger = get_logger(__name__)

# Ensure DB schema exists on first import
try:
    init_db()
except Exception as _e:
    logger.warning("DB init failed: %s", _e)


class ScenarioEngine:
    def __init__(
        self,
        on_step_start: Optional[Callable[[int, Step], None]] = None,
        on_step_done: Optional[Callable[[int, Step], None]] = None,
        on_finished: Optional[Callable[[bool], None]] = None,
    ):
        self._tracker = RunTracker()
        self._user_on_step_start = on_step_start
        self._user_on_step_done = on_step_done
        self._player = Player(
            on_step_start=self._on_step_start,
            on_step_done=self._on_step_done,
            on_step_error=self._on_step_error,
            on_finished=self._handle_finished,
        )
        self._on_finished = on_finished
        self._scenario: Optional[Scenario] = None

    @property
    def is_running(self) -> bool:
        return self._player.is_running

    def load_from_file(self, path: str | Path) -> Scenario:
        self._scenario = load_scenario(path)
        logger.info("Loaded scenario '%s' (%d steps)", self._scenario.name, len(self._scenario.steps))
        return self._scenario

    def load_scenario(self, scenario: Scenario) -> None:
        self._scenario = scenario
        logger.info("Loaded scenario '%s' (%d steps)", scenario.name, len(scenario.steps))

    def run(self) -> None:
        if self._scenario is None:
            raise RuntimeError("No scenario loaded. Call load_scenario() first.")
        if self._player.is_running:
            logger.warning("Engine is already running.")
            return
        logger.info("Starting scenario '%s'", self._scenario.name)
        self._tracker.start(
            scenario_id=self._scenario.id or self._scenario.name,
            scenario_name=self._scenario.name,
            total_steps=len(self._scenario.steps),
        )
        self._player.play(self._scenario.steps)

    def stop(self) -> None:
        logger.info("Stop requested.")
        self._player.stop()

    # ── Internal callbacks ────────────────────────────────────────────────────

    def _on_step_start(self, index: int, step: Step) -> None:
        self._tracker.on_step_start(index, step)
        if self._user_on_step_start:
            self._user_on_step_start(index, step)

    def _on_step_done(self, index: int, step: Step) -> None:
        self._tracker.on_step_done(index, step)
        if self._user_on_step_done:
            self._user_on_step_done(index, step)

    def _on_step_error(self, index: int, step: Step, error: str) -> None:
        self._tracker.on_step_error(index, step, error)

    def _handle_finished(self, success: bool) -> None:
        status = "SUCCESS" if success else "FAILED/STOPPED"
        logger.info("Scenario finished: %s", status)
        self._tracker.finish(success)
        if self._on_finished:
            self._on_finished(success)
