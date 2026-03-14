"""
Action executors: translate ActionStep into real OS input.
Uses pynput for mouse and keyboard simulation.
"""
from __future__ import annotations
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

from app.core.models import ActionStep, ActionType

_mouse = MouseController()
_keyboard = KeyboardController()

_BUTTON_MAP = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

_SPECIAL_KEYS = {
    "Key.enter": Key.enter,
    "Key.space": Key.space,
    "Key.tab": Key.tab,
    "Key.backspace": Key.backspace,
    "Key.delete": Key.delete,
    "Key.esc": Key.esc,
    "Key.shift": Key.shift,
    "Key.ctrl_l": Key.ctrl_l,
    "Key.ctrl_r": Key.ctrl_r,
    "Key.alt_l": Key.alt_l,
    "Key.alt_r": Key.alt_r,
    "Key.up": Key.up,
    "Key.down": Key.down,
    "Key.left": Key.left,
    "Key.right": Key.right,
}


def execute_action(step: ActionStep) -> None:
    if step.action_type == ActionType.MOUSE_CLICK:
        _do_mouse_click(step)
    elif step.action_type == ActionType.MOUSE_MOVE:
        _do_mouse_move(step)
    elif step.action_type == ActionType.MOUSE_SCROLL:
        _do_mouse_scroll(step)
    elif step.action_type == ActionType.KEY_PRESS:
        _do_key_press(step)
    elif step.action_type == ActionType.TYPE_TEXT:
        _do_type_text(step)


def _do_mouse_click(step: ActionStep) -> None:
    if step.x is not None and step.y is not None:
        _mouse.position = (step.x, step.y)
    btn = _BUTTON_MAP.get(step.button, Button.left)
    _mouse.click(btn)


def _do_mouse_move(step: ActionStep) -> None:
    if step.x is not None and step.y is not None:
        _mouse.position = (step.x, step.y)


def _do_mouse_scroll(step: ActionStep) -> None:
    if step.x is not None and step.y is not None:
        _mouse.position = (step.x, step.y)
    _mouse.scroll(step.dx, step.dy)


def _do_key_press(step: ActionStep) -> None:
    if not step.key:
        return
    key = _SPECIAL_KEYS.get(step.key, step.key)
    _keyboard.press(key)
    _keyboard.release(key)


def _do_type_text(step: ActionStep) -> None:
    if step.text:
        _keyboard.type(step.text)
