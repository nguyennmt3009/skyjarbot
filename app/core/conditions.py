"""
Condition evaluators.
Each evaluator polls until the condition is satisfied or times out.
"""
from __future__ import annotations
import time

from app.core.models import ConditionStep, ConditionType
from app.platform.screen_capture import (
    get_pixel_color, color_matches,
    capture_region, capture_region_as_array,
    capture_full_screen, capture_full_screen_as_array,
)


class ConditionTimeoutError(Exception):
    pass


def evaluate_condition(step: ConditionStep) -> bool:
    """
    Block until condition is satisfied or timeout is reached.
    Returns True if satisfied, raises ConditionTimeoutError otherwise.
    """
    if step.condition_type == ConditionType.PIXEL_COLOR:
        return _wait_pixel_color(step)
    if step.condition_type == ConditionType.IMAGE_MATCH:
        return _wait_image_match(step)
    if step.condition_type == ConditionType.OCR_TEXT:
        return _wait_ocr_text(step)
    raise NotImplementedError(f"Unsupported condition type: {step.condition_type}")


def _wait_pixel_color(step: ConditionStep) -> bool:
    deadline = time.monotonic() + step.timeout_ms / 1000.0
    interval = step.poll_interval_ms / 1000.0

    while time.monotonic() < deadline:
        actual = get_pixel_color(step.x, step.y)
        if color_matches(actual, step.expected_color, step.tolerance):
            return True
        time.sleep(interval)

    raise ConditionTimeoutError(
        f"Pixel at ({step.x}, {step.y}) did not match "
        f"{step.expected_color} within {step.timeout_ms} ms"
    )


def _wait_image_match(step: ConditionStep) -> bool:
    import cv2
    import numpy as np

    template_bgr = cv2.imread(step.template_path, cv2.IMREAD_COLOR)
    if template_bgr is None:
        raise FileNotFoundError(f"Template image not found: {step.template_path!r}")

    deadline = time.monotonic() + step.timeout_ms / 1000.0
    interval = step.poll_interval_ms / 1000.0

    while time.monotonic() < deadline:
        if step.search_region:
            x, y, w, h = step.search_region
            frame_rgb = capture_region_as_array(x, y, w, h)
        else:
            frame_rgb = capture_full_screen_as_array()

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(frame_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val >= step.match_threshold:
            return True
        time.sleep(interval)

    raise ConditionTimeoutError(
        f"Template '{step.template_path}' not matched (threshold={step.match_threshold}) "
        f"within {step.timeout_ms} ms"
    )


def _wait_ocr_text(step: ConditionStep) -> bool:
    import pytesseract

    deadline = time.monotonic() + step.timeout_ms / 1000.0
    interval = step.poll_interval_ms / 1000.0

    while time.monotonic() < deadline:
        if step.ocr_region:
            x, y, w, h = step.ocr_region
            img = capture_region(x, y, w, h)
        else:
            img = capture_full_screen()

        detected = pytesseract.image_to_string(img).strip()

        if step.ocr_contains:
            matched = step.expected_text.lower() in detected.lower()
        else:
            matched = detected.lower() == step.expected_text.lower()

        if matched:
            return True
        time.sleep(interval)

    raise ConditionTimeoutError(
        f"OCR text '{step.expected_text}' not found within {step.timeout_ms} ms"
    )
