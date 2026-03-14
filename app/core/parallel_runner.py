"""
ParallelRunner: executes multiple scenarios concurrently using threads.
Each scenario runs in its own ScenarioEngine instance.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from app.core.models import Scenario
from app.core.serializer import load_scenario
from app.core.logger_service import get_logger

logger = get_logger(__name__)


@dataclass
class RunSlot:
    scenario: Scenario
    status: str = "pending"       # pending | running | passed | failed | stopped
    error: str  = ""
    on_status_change: Optional[Callable[["RunSlot"], None]] = field(default=None, repr=False)

    def _set_status(self, status: str, error: str = "") -> None:
        self.status = status
        self.error  = error
        if self.on_status_change:
            self.on_status_change(self)


class ParallelRunner:
    """
    Load N scenarios and run them all simultaneously.
    Each slot gets its own Player + thread so they don't block each other.
    """

    def __init__(self) -> None:
        self._slots: list[RunSlot] = []
        self._engines: list = []
        self._done_event = threading.Event()

    # ── Public API ────────────────────────────────────────────────────────────

    def add_scenario_file(
        self,
        path: str | Path,
        on_status_change: Optional[Callable[[RunSlot], None]] = None,
    ) -> RunSlot:
        scenario = load_scenario(path)
        slot = RunSlot(scenario=scenario, on_status_change=on_status_change)
        self._slots.append(slot)
        return slot

    def add_scenario(
        self,
        scenario: Scenario,
        on_status_change: Optional[Callable[[RunSlot], None]] = None,
    ) -> RunSlot:
        slot = RunSlot(scenario=scenario, on_status_change=on_status_change)
        self._slots.append(slot)
        return slot

    def run_all(self, on_all_done: Optional[Callable[[list[RunSlot]], None]] = None) -> None:
        if not self._slots:
            return
        self._done_event.clear()
        self._engines.clear()
        remaining = [len(self._slots)]
        lock = threading.Lock()

        for slot in self._slots:
            engine = self._make_engine(slot, remaining, lock, on_all_done)
            self._engines.append(engine)
            engine.load_scenario(slot.scenario)

        logger.info("ParallelRunner: starting %d scenarios", len(self._slots))
        for engine in self._engines:
            engine.run()

    def stop_all(self) -> None:
        for engine in self._engines:
            engine.stop()

    def clear(self) -> None:
        self._slots.clear()
        self._engines.clear()

    @property
    def slots(self) -> list[RunSlot]:
        return list(self._slots)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _make_engine(
        self,
        slot: RunSlot,
        remaining: list[int],
        lock: threading.Lock,
        on_all_done: Optional[Callable],
    ):
        from app.core.scenario_engine import ScenarioEngine

        def on_finished(success: bool) -> None:
            slot._set_status("passed" if success else "failed")
            with lock:
                remaining[0] -= 1
                if remaining[0] == 0:
                    logger.info("ParallelRunner: all scenarios finished")
                    if on_all_done:
                        on_all_done(self._slots)

        engine = ScenarioEngine(on_finished=on_finished)
        slot._set_status("pending")

        # Patch run() to update status to running
        original_run = engine.run

        def patched_run() -> None:
            slot._set_status("running")
            original_run()

        engine.run = patched_run
        return engine
