# SkyjarBot — Technical Update (v0.2)

Date: 2026-03-19

---

## 1. Overview

This document describes new features and changes added in version 0.2.

Three improvements were made:

* LightShot-style screen coordinate picker
* Random delay range for DelayStep
* Runtime data excluded from version control

---

## 2. Screen Coordinate Picker

### 2.1 Problem

The Add Step Dialog previously required users to type pixel coordinates manually as integers.
The existing "Sample pixel from screen" button used a blind 3-second countdown with no visual feedback.
Entering region values (x,y,w,h) as a comma-separated string was error-prone and unintuitive.

---

### 2.2 Solution

A fullscreen overlay is displayed when the user clicks a picker button.
The overlay captures a screenshot, displays it as the background, and applies a dark tint.
The user can click to select a point or drag to select a rectangular region.
Coordinates are filled into the dialog fields automatically after selection.

The UX is inspired by LightShot.

---

### 2.3 New File: `app/ui/screen_picker.py`

**Class:** `ScreenPickerOverlay(tk.Toplevel)`

Behavior:

* Takes a full-screen screenshot using `PIL.ImageGrab.grab()` before the overlay window appears.
* Creates a borderless, topmost, fullscreen window using `overrideredirect=True`.
* Displays the screenshot as the Canvas background image.
* Covers the entire screen with four dark tint rectangles (`fill=black`, `stipple=gray50`).
* A coordinate label follows the cursor showing current `(x, y)`.
* On drag: the four tint rectangles reposition to expose the selected area. A cyan border (`#00d4ff`) is drawn around the selection. The label updates to show `(x, y)  W × H`.
* On click (no drag): returns `(x, y)`.
* On release after drag: returns `(x, y, w, h)`.
* On ESC: returns `None`.

Two modes:

| Mode | Returns |
|---|---|
| `point` | `(x, y)` |
| `region` | `(x, y, w, h)` on drag, `(x, y)` on click |

---

### 2.4 Changes to `app/ui/add_step_dialog.py`

Added `_open_picker(mode, on_done)` helper:

* Releases the modal grab and hides the dialog.
* Waits 150 ms before launching the overlay, ensuring the dialog disappears before the screenshot is taken.
* After selection, restores the dialog and re-applies the modal grab.

Added picker buttons:

| Panel | Button | Action |
|---|---|---|
| Action (click / move / scroll) | 🎯 Pick point | Fills X, Y |
| Condition → Pixel Color | 🎯 Pick & sample pixel | Fills X, Y and samples R, G, B automatically |
| Condition → Image Match | 🎯 Pick region | Fills search_region as `x,y,w,h` |
| Condition → OCR Text | 🎯 Pick region | Fills ocr_region as `x,y,w,h` |
| Branch | 🎯 Pick point | Fills X, Y |

The Pick point button in the Action panel is automatically hidden when the action type does not use coordinates (KEY_PRESS, TYPE_TEXT).

The old `_sample_pixel()` and `_apply_sample()` methods were removed and fully replaced by the new picker.

---

## 3. Random Delay Range

### 3.1 Problem

`DelayStep` only supported a fixed duration. Uniform timing makes automation easier to detect and less resilient to variable system load.

---

### 3.2 Solution

Added an optional `duration_max_ms` field to `DelayStep`.
If set, the actual delay at runtime is chosen randomly between `duration_ms` and `duration_max_ms`.
If not set, behavior is identical to the previous fixed delay.

---

### 3.3 Changes

**`app/core/models.py`**

```python
@dataclass
class DelayStep:
    step_type: StepType = field(default=StepType.DELAY, init=False)
    duration_ms: int = 1000
    duration_max_ms: Optional[int] = None   # if set: actual delay = random(min, max)
```

**`app/core/player.py`**

```python
if step.duration_max_ms is not None and step.duration_max_ms > step.duration_ms:
    actual_ms = random.randint(step.duration_ms, step.duration_max_ms)
else:
    actual_ms = step.duration_ms
```

**`app/core/serializer.py`**

* Serialize: `duration_max_ms` is written to JSON only when not `None`.
* Deserialize: reads `duration_max_ms` from JSON. Field absence is treated as `None`. Existing scenario files remain valid without modification.

**`app/ui/add_step_dialog.py`**

* Delay panel: renamed "Duration (ms)" label to "Min (ms)". Added "Max (ms)" field with hint "leave blank for fixed delay".
* `_build_step`: sets `duration_max_ms` only when the Max field is not empty.

**`app/ui/main_window.py`**

* Step list display: shows `delay 500–1500 ms (random)` when a range is configured, `delay 1000 ms` for fixed delay.

---

## 4. Runtime Data Excluded from Version Control

### 4.1 Problem

`app/data/scenarios/` was not excluded from git. Scenario files contain machine-specific pixel coordinates and are not meaningful across different machines or users. The database and log files are also runtime artifacts.

---

### 4.2 Changes to `.gitignore`

```
# Runtime data (machine-specific, not source code)
app/data/scenarios/
app/data/*.db
logs/
reports/
```

---

## 5. Files Changed

| File | Type | Summary |
|---|---|---|
| `app/ui/screen_picker.py` | New | LightShot-style fullscreen coordinate picker |
| `app/ui/add_step_dialog.py` | Modified | 🎯 picker buttons, random delay UI |
| `app/core/models.py` | Modified | `DelayStep.duration_max_ms` field |
| `app/core/player.py` | Modified | Random delay execution logic |
| `app/core/serializer.py` | Modified | Serialize / deserialize `duration_max_ms` |
| `app/ui/main_window.py` | Modified | Step list label for random delay |
| `.gitignore` | Modified | Exclude scenarios, database, logs, reports |
