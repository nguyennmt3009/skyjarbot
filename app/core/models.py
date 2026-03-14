from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class StepType(str, Enum):
    ACTION = "action"
    CONDITION = "condition"
    DELAY = "delay"


class ActionType(str, Enum):
    MOUSE_CLICK = "click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    TYPE_TEXT = "type_text"


class ConditionType(str, Enum):
    PIXEL_COLOR = "pixel_color"


@dataclass
class ActionStep:
    step_type: StepType = field(default=StepType.ACTION, init=False)
    action_type: ActionType = ActionType.MOUSE_CLICK
    x: Optional[int] = None
    y: Optional[int] = None
    button: str = "left"        # for mouse click
    key: Optional[str] = None   # for key press
    text: Optional[str] = None  # for type_text
    dx: int = 0                 # for mouse_scroll
    dy: int = 0


@dataclass
class ConditionStep:
    step_type: StepType = field(default=StepType.CONDITION, init=False)
    condition_type: ConditionType = ConditionType.PIXEL_COLOR
    x: int = 0
    y: int = 0
    expected_color: Tuple[int, int, int] = (0, 0, 0)
    tolerance: int = 10
    timeout_ms: int = 5000
    poll_interval_ms: int = 200


@dataclass
class DelayStep:
    step_type: StepType = field(default=StepType.DELAY, init=False)
    duration_ms: int = 1000


Step = ActionStep | ConditionStep | DelayStep


@dataclass
class Scenario:
    id: str = ""
    name: str = ""
    description: str = ""
    version: int = 1
    steps: List[Step] = field(default_factory=list)
