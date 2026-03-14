"""
Screen capture utilities using Pillow (PIL).
"""
from __future__ import annotations
from typing import Tuple, Optional
import PIL.ImageGrab
import PIL.Image


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


def capture_region(x: int, y: int, w: int, h: int) -> PIL.Image.Image:
    """Capture a rectangular region of the screen and return a PIL Image (RGB)."""
    img = PIL.ImageGrab.grab(bbox=(x, y, x + w, y + h))
    return img.convert("RGB")


def capture_region_as_array(x: int, y: int, w: int, h: int):
    """Capture a screen region and return a numpy ndarray in RGB format."""
    import numpy as np
    return np.array(capture_region(x, y, w, h))


def capture_full_screen() -> PIL.Image.Image:
    """Capture the entire primary screen and return a PIL Image (RGB)."""
    return PIL.ImageGrab.grab().convert("RGB")


def capture_full_screen_as_array():
    """Capture the full screen and return a numpy ndarray in RGB format."""
    import numpy as np
    return np.array(capture_full_screen())
