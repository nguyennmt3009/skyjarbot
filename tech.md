# Macro Recorder & Blackbox UI Testing Tool

Technical Design Document (v0.1)

## 1. Project Overview

### 1.1 Purpose

This project aims to build a **desktop automation and blackbox UI testing tool** for Windows.

The application can:

* Record mouse and keyboard actions.
* Replay recorded actions.
* Observe screen conditions before executing the next step.
* Execute test scenarios dynamically based on screen state.
* Collect runtime data and logs for later analysis.

The long-term goal is to evolve this project into a **flexible blackbox UI testing framework**.

---

### 1.2 Target Platform

* OS: Windows 10 / Windows 11
* Language: Python 3.11+
* Desktop UI: PySide6 or Tkinter
* Execution: Local desktop automation

---

### 1.3 Key Capabilities (Long-term Vision)

The tool should eventually support:

* Macro recording
* Scenario-based automation
* Screen observation (pixel / image / OCR)
* Conditional branching
* Runtime data collection
* Execution logs
* Test reporting
* Scenario management
* Blackbox UI testing

---

## 2. Scope

### 2.1 Version 1 Scope (done)

The first version will focus on building the **core automation engine**.

Features included:

* Record keyboard and mouse actions (done)
* Playback recorded actions (done)
* Basic scenario execution engine (done)
* Pixel color condition (done)
* Save and load scenarios using JSON (done)
* Simple desktop UI (done)
* Execution logging (done)

---

### 2.2 Out of Scope (Version 1)

The following features will **not be implemented in the first version**:

* OCR text detection
* Image template matching
* Advanced branching logic
* Database storage
* Test reporting dashboard
* Multi-user scenario management
* Cloud synchronization
* Visual scenario editor

---

## 3. System Architecture

The system is divided into several logical modules.

```
app/
  main.py

  ui/
    main_window.py

  core/
    models.py
    recorder.py
    player.py
    scenario_engine.py
    actions.py
    conditions.py
    serializer.py
    logger_service.py

  platform/
    input_hooks.py
    screen_capture.py

  data/
    scenarios/
```

---

### 3.1 UI Layer

Responsible for:

* Displaying controls
* Triggering record/playback
* Showing logs
* Managing scenario files

UI should remain **thin** and delegate logic to core modules.

---

### 3.2 Core Engine

Contains the core logic of the automation framework.

Responsibilities:

* Scenario definition
* Step execution
* Condition evaluation
* Action execution
* Logging

The core engine should **not depend on UI code**.

---

### 3.3 Platform Layer

Handles OS-level interaction.

Examples:

* Keyboard and mouse hooks
* Input simulation
* Screen capture

This layer isolates OS-specific behavior.

---

### 3.4 Storage Layer

Initial version uses **JSON files** for scenario persistence.

Future versions may add:

* SQLite
* Run history storage
* Reporting data

---

## 4. Core Data Models

### 4.1 Scenario

Represents a complete automation workflow.

Fields:

* id
* name
* description
* steps
* version

---

### 4.2 Step

Base unit of execution.

Types:

* ActionStep
* ConditionStep
* DelayStep

---

### 4.3 ActionStep

Performs a direct action.

Examples:

* mouse click
* key press
* typing text
* waiting

---

### 4.4 ConditionStep

Checks a condition before continuing.

Examples:

* pixel color check
* image match
* OCR text detection

---

### 4.5 DelayStep

Waits for a fixed amount of time.

---

## 5. Scenario Execution Engine

The **Scenario Engine** executes steps sequentially.

Execution flow:

1. Load scenario
2. Iterate through steps
3. Execute step
4. Evaluate conditions
5. Continue or stop based on result

Pseudo flow:

```
for step in scenario.steps:
    if step is ConditionStep:
        wait until condition satisfied or timeout
    elif step is ActionStep:
        perform action
    elif step is DelayStep:
        sleep
```

---

## 6. Screen Observation

Initial version supports:

### PixelColorCondition

Checks if a screen pixel matches an expected color.

Fields:

* x
* y
* expected_color
* tolerance
* timeout_ms
* poll_interval_ms

Example usage:

```
wait until pixel(100,200) ≈ (255,0,0)
timeout: 5000 ms
```

---

## 7. Logging

The system should produce structured logs.

Logs should include:

* step execution
* condition evaluation
* errors
* scenario start/end

Logging should use Python's built-in **logging module**.

---

## 8. Scenario Serialization

Scenarios are stored as JSON.

Example:

```json
{
  "name": "simple_test",
  "version": 1,
  "steps": [
    {
      "type": "click",
      "x": 500,
      "y": 300
    },
    {
      "type": "pixel_condition",
      "x": 200,
      "y": 150,
      "color": [255,0,0],
      "timeout_ms": 3000
    }
  ]
}
```

---

## 9. Development Roadmap

### Phase 1 — Core Macro Engine (done)

Goals:

* Basic UI (done)
* Record mouse/keyboard (done)
* Playback events (done)
* Save/load JSON (done)

---

### Phase 2 — Scenario Engine (done)

Goals:

* Step model (done)
* ActionStep (done)
* ConditionStep (done)
* DelayStep (done)
* Pixel condition (done)

---

### Phase 3 — Screen Intelligence (done)

Goals:

* OCR support (done)
* Image template matching (done)
* Region capture (done)

Libraries considered:

* pytesseract (done)
* OpenCV (done)
https://github.com/UB-Mannheim/tesseract/wiki
---

### Phase 4 — Data & Reporting (done)

Goals:

* Database storage (done)
* Execution history (done)
* Scenario statistics (done)
* Test reports (done)

Possible database:

* SQLite (done)

---

### Phase 5 — Advanced Automation

Potential future features:

* branching logic
* variables
* reusable scenario blocks
* parallel test execution
* visual scenario editor

---

## 10. Technical Risks

Possible challenges:

* Screen DPI scaling
* Different display resolutions
* Timing inconsistencies
* OCR accuracy
* Automation reliability
* Multi-monitor setups

Mitigation strategies will be introduced gradually.

---

## 11. Design Principles

Key principles for development:

* Keep architecture modular
* Separate UI from core logic
* Avoid premature optimization
* Prefer simplicity over complexity
* Ensure extensibility for future testing features

---

## 12. Next Steps

Immediate tasks:

1. Implement Phase 1 features (done)
2. Build project skeleton (done)
3. Implement Recorder module (done)
4. Implement Player module (done)
5. Add scenario serialization (done)
6. Create minimal UI (done)

After Phase 1 is stable, development will move to Phase 2.
