"""
Data models for run history and step results.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class StepRecord:
    step_index: int
    step_type: str
    description: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    success: bool = True
    error_msg: str = ""

    @property
    def duration_ms(self) -> Optional[float]:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds() * 1000
        return None


@dataclass
class RunRecord:
    scenario_id: str
    scenario_name: str
    started_at: datetime
    id: int = 0
    finished_at: Optional[datetime] = None
    success: bool = False
    total_steps: int = 0
    steps_done: int = 0
    steps: List[StepRecord] = field(default_factory=list)

    @property
    def duration_s(self) -> Optional[float]:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
