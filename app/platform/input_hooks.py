"""
Keyboard and mouse hooks using pynput.
Records raw input events and emits them via callbacks.
"""
from __future__ import annotations
from typing import Callable, Optional
from pynput import mouse, keyboard


class InputHooks:
    """Listens to global mouse and keyboard events and forwards them to callbacks."""

    def __init__(
        self,
        on_mouse_click: Optional[Callable] = None,
        on_mouse_move: Optional[Callable] = None,
        on_mouse_scroll: Optional[Callable] = None,
        on_key_press: Optional[Callable] = None,
        on_key_release: Optional[Callable] = None,
    ):
        self._on_mouse_click = on_mouse_click
        self._on_mouse_move = on_mouse_move
        self._on_mouse_scroll = on_mouse_scroll
        self._on_key_press = on_key_press
        self._on_key_release = on_key_release

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None

    def start(self) -> None:
        self._mouse_listener = mouse.Listener(
            on_click=self._handle_click,
            on_move=self._handle_move,
            on_scroll=self._handle_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._handle_key_press,
            on_release=self._handle_key_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self) -> None:
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _handle_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if self._on_mouse_click and pressed:
            self._on_mouse_click(x, y, button.name)

    def _handle_move(self, x: int, y: int) -> None:
        if self._on_mouse_move:
            self._on_mouse_move(x, y)

    def _handle_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if self._on_mouse_scroll:
            self._on_mouse_scroll(x, y, dx, dy)

    def _handle_key_press(self, key) -> None:
        if self._on_key_press:
            key_str = key.char if hasattr(key, "char") and key.char else str(key)
            self._on_key_press(key_str)

    def _handle_key_release(self, key) -> None:
        if self._on_key_release:
            key_str = key.char if hasattr(key, "char") and key.char else str(key)
            self._on_key_release(key_str)
