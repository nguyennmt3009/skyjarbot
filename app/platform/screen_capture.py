"""
Screen capture utilities using Pillow (PIL).
"""
from __future__ import annotations
from typing import Tuple
import PIL.ImageGrab


def get_pixel_color(x: int, y: int) -> Tuple[int, int, int]:
    """Return the RGB color of the pixel at screen coordinates (x, y)."""
    screenshot = PIL.ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    r, g, b = screenshot.getpixel((0, 0))[:3]
    return (r, g, b)


def color_matches(
    actual: Tuple[int, int, int],
    expected: Tuple[int, int, int],
    tolerance: int = 10,
) -> bool:
    """Check whether two RGB colors are within tolerance of each other."""
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))
