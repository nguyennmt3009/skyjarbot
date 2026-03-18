"""
LightShot-style fullscreen overlay for picking screen coordinates or regions.

Usage:
    overlay = ScreenPickerOverlay(parent, mode="point", callback=fn)
    # fn((x, y))       on click
    # fn(None)         on ESC / cancel

    overlay = ScreenPickerOverlay(parent, mode="region", callback=fn)
    # fn((x, y, w, h)) on drag
    # fn((x, y))       on click (no drag)
    # fn(None)         on ESC / cancel
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Tuple, Union

from PIL import ImageGrab, ImageTk

_TINT        = "#000000"
_TINT_STIPPLE = "gray50"
_BORDER      = "#00d4ff"
_LABEL_BG    = "#1a1a2e"
_LABEL_FG    = "#00d4ff"
_HELP_FG     = "#ffffff"
_DRAG_THRESH = 5          # px before drag mode activates


class ScreenPickerOverlay(tk.Toplevel):
    """
    Fullscreen screenshot overlay.

    Draws a dark tint over the entire screen.
    While dragging, the selected rectangle is revealed (tint removed inside).
    A coordinate label follows the cursor.
    """

    def __init__(
        self,
        parent: tk.Widget,
        mode: str,
        callback: Callable[
            [Optional[Union[Tuple[int, int], Tuple[int, int, int, int]]]], None
        ],
    ):
        super().__init__(parent)
        self._mode     = mode       # "point" or "region"
        self._callback = callback

        self._start_x: Optional[int] = None
        self._start_y: Optional[int] = None
        self._dragging = False
        self._done     = False

        # Capture screenshot BEFORE the overlay window is shown
        self._screenshot = ImageGrab.grab()
        self._sw = self._screenshot.width
        self._sh = self._screenshot.height

        self._setup_window()
        self._build_canvas()
        self._bind_events()
        self.focus_force()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.overrideredirect(True)           # no title bar / borders
        self.attributes("-topmost", True)
        self.geometry(f"{self._sw}x{self._sh}+0+0")

    # ── Canvas ────────────────────────────────────────────────────────────────

    def _build_canvas(self) -> None:
        # Keep a reference so it isn't garbage-collected
        self._tk_img = ImageTk.PhotoImage(self._screenshot)

        c = tk.Canvas(
            self,
            width=self._sw, height=self._sh,
            highlightthickness=0,
            cursor="crosshair",
        )
        c.pack(fill="both", expand=True)
        self._c = c

        W, H = self._sw, self._sh

        # Layer 1 – original screenshot as background
        c.create_image(0, 0, anchor="nw", image=self._tk_img)

        # Layer 2 – four dark tint rectangles (initially cover full screen)
        kw = dict(fill=_TINT, stipple=_TINT_STIPPLE, outline="")
        self._r_top    = c.create_rectangle(0, 0, W, H,  **kw)
        self._r_bottom = c.create_rectangle(0, H, W, H,  **kw)
        self._r_left   = c.create_rectangle(0, 0, 0, H,  **kw)
        self._r_right  = c.create_rectangle(W, 0, W, H,  **kw)

        # Layer 3 – selection border (initially zero-size / invisible)
        self._sel = c.create_rectangle(0, 0, 0, 0, outline=_BORDER, width=2)

        # Layer 4 – coordinate label (tk.Label inside canvas window for bg support)
        self._lbl_var = tk.StringVar()
        self._lbl_widget = tk.Label(
            c,
            textvariable=self._lbl_var,
            bg=_LABEL_BG, fg=_LABEL_FG,
            font=("Consolas", 11, "bold"),
            padx=6, pady=3,
        )
        self._lbl_win = c.create_window(20, 20, anchor="nw", window=self._lbl_widget)

        # Help text at bottom
        if self._mode == "point":
            help_text = "Click to pick a point   |   ESC to cancel"
        else:
            help_text = (
                "Click to pick a point   |   Drag to select a region   |   ESC to cancel"
            )
        c.create_text(
            W // 2, H - 28, anchor="center",
            text=help_text, fill=_HELP_FG,
            font=("Consolas", 11),
        )

    # ── Events ────────────────────────────────────────────────────────────────

    def _bind_events(self) -> None:
        self._c.bind("<Motion>",          self._on_motion)
        self._c.bind("<ButtonPress-1>",   self._on_press)
        self._c.bind("<B1-Motion>",       self._on_drag)
        self._c.bind("<ButtonRelease-1>", self._on_release)
        self._c.bind("<Escape>",          lambda _: self._cancel())
        self.bind("<Escape>",             lambda _: self._cancel())

    def _on_motion(self, e: tk.Event) -> None:
        if not self._dragging:
            self._update_label(e.x, e.y)

    def _on_press(self, e: tk.Event) -> None:
        self._start_x = e.x
        self._start_y = e.y
        self._dragging = False

    def _on_drag(self, e: tk.Event) -> None:
        if self._start_x is None:
            return
        if (abs(e.x - self._start_x) > _DRAG_THRESH
                or abs(e.y - self._start_y) > _DRAG_THRESH):
            self._dragging = True
        if self._dragging:
            self._draw_tint_with_selection(self._start_x, self._start_y, e.x, e.y)
            self._update_label(e.x, e.y, self._start_x, self._start_y)

    def _on_release(self, e: tk.Event) -> None:
        if self._done:
            return
        self._done = True
        if self._mode == "point" or not self._dragging:
            self._finish((e.x, e.y))
        else:
            x1 = min(self._start_x, e.x)
            y1 = min(self._start_y, e.y)
            w  = abs(e.x - self._start_x)
            h  = abs(e.y - self._start_y)
            self._finish((x1, y1, w, h) if w > 1 and h > 1 else (e.x, e.y))

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_tint_with_selection(
        self, x1: int, y1: int, x2: int, y2: int
    ) -> None:
        """Reposition the 4 tint rects so the selection rect is unobscured."""
        sx1, sx2 = min(x1, x2), max(x1, x2)
        sy1, sy2 = min(y1, y2), max(y1, y2)
        W, H = self._sw, self._sh
        self._c.coords(self._r_top,    0,   0,   W,   sy1)
        self._c.coords(self._r_bottom, 0,   sy2, W,   H)
        self._c.coords(self._r_left,   0,   sy1, sx1, sy2)
        self._c.coords(self._r_right,  sx2, sy1, W,   sy2)
        self._c.coords(self._sel,      sx1, sy1, sx2, sy2)

    def _update_label(
        self, x: int, y: int,
        sx: Optional[int] = None, sy: Optional[int] = None,
    ) -> None:
        if sx is not None and sy is not None:
            w = abs(x - sx)
            h = abs(y - sy)
            text = f"({min(x, sx)}, {min(y, sy)})   {w} × {h}"
        else:
            text = f"({x}, {y})"
        self._lbl_var.set(text)

        # Offset from cursor; flip sides near screen edges
        lx, ly = x + 18, y + 18
        est_w = len(text) * 8 + 14   # rough pixel width at Consolas 11
        if lx + est_w > self._sw:
            lx = x - est_w - 4
        if ly + 30 > self._sh:
            ly = y - 40
        self._c.coords(self._lbl_win, lx, ly)

    # ── Finish ────────────────────────────────────────────────────────────────

    def _cancel(self) -> None:
        if not self._done:
            self._done = True
            self._finish(None)

    def _finish(self, result) -> None:
        self.destroy()
        self._callback(result)
