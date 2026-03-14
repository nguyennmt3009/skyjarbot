from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class StepType(str, Enum):
    ACTION        = "action"
    CONDITION     = "condition"
    DELAY         = "delay"
    BRANCH        = "branch"
    SET_VARIABLE  = "set_variable"
    CALL_SCENARIO = "call_scenario"


class ActionType(str, Enum):
    MOUSE_CLICK = "click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    TYPE_TEXT = "type_text"


class ConditionType(str, Enum):
    PIXEL_COLOR = "pixel_color"
    IMAGE_MATCH = "image_match"
    OCR_TEXT    = "ocr_text"


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
    timeout_ms: int = 5000
    poll_interval_ms: int = 200

    # pixel_color fields
    x: int = 0
    y: int = 0
    expected_color: Tuple[int, int, int] = (0, 0, 0)
    tolerance: int = 10

    # image_match fields
    template_path: str = ""
    match_threshold: float = 0.8
    search_region: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h

    # ocr_text fields
    ocr_region: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    expected_text: str = ""
    ocr_contains: bool = True   # True = substring match, False = exact match


@dataclass
class DelayStep:
    step_type: StepType = field(default=StepType.DELAY, init=False)
    duration_ms: int = 1000


@dataclass
class BranchStep:
    """If condition → run on_true steps, else → run on_false steps."""
    step_type: StepType = field(default=StepType.BRANCH, init=False)
    condition: ConditionStep = field(default_factory=ConditionStep)
    on_true:  List = field(default_factory=list)   # List[Step]
    on_false: List = field(default_factory=list)   # List[Step]


@dataclass
class SetVariableStep:
    """Set a named variable. Value can contain {other_var} references."""
    step_type: StepType = field(default=StepType.SET_VARIABLE, init=False)
    name:  str = ""
    value: str = ""   # literal or expression like "{counter}"


@dataclass
class CallScenarioStep:
    """Load and execute another scenario file inline."""
    step_type: StepType = field(default=StepType.CALL_SCENARIO, init=False)
    scenario_path: str = ""


Step = ActionStep | ConditionStep | DelayStep | BranchStep | SetVariableStep | CallScenarioStep


@dataclass
class Scenario:
    id: str = ""
    name: str = ""
    description: str = ""
    version: int = 1
    steps: List[Step] = field(default_factory=list)
