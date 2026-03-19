# SkyjarBot — Technical Plan v0.3: Block-Based Visual Editor

Date: 2026-03-19

---

## 1. Vấn đề hiện tại

| # | Vấn đề |
|---|---|
| 1 | Steps hiển thị dạng flat list — không thấy cấu trúc lồng nhau |
| 2 | Branch (if/else) sub-steps chỉ chỉnh được qua JSON thủ công |
| 3 | Không có kéo-thả để sắp xếp lại thứ tự |
| 4 | Loop chưa tồn tại trong UI |
| 5 | Tkinter khó tùy chỉnh visual, không có animation |

---

## 2. Mục tiêu

Xây dựng **Block Editor** — giao diện khối dọc có thể nest, kéo thả, màu pastel dễ thương, thay thế hoàn toàn flat list hiện tại.

**Hình mẫu tham chiếu**: Alice (event block list), Scratch (khối màu, lồng nhau) — nhưng **không phải canvas tự do**, mà là **danh sách dọc có cấu trúc**.

**Không thay đổi**: core engine, models, serializer, player, recorder — tất cả giữ nguyên.

---

## 3. Framework: PySide6 (Qt6)

Chuyển từ Tkinter → **PySide6** vì:
- Custom widget tốt hơn (paintEvent, QSS styling)
- Drag & drop native (QDrag, QDropEvent)
- Layout linh hoạt hơn cho block nesting
- Đã nằm trong roadmap Phase 6

Thêm dependency:
```
PySide6>=6.6.0
```

---

## 4. Thiết kế UI

### 4.1 Layout tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│  [▶ Play] [⏺ Record] [💾 Save] [📂 Load] [🗑 Clear]  Toolbar    │
├──────────────┬──────────────────────────────┬───────────────────┤
│   PALETTE    │        BLOCK EDITOR          │   STATUS / LOG    │
│              │                              │                   │
│  ┌─────────┐ │  ┌──────────────────────┐   │  Execution log    │
│  │ Actions │ │  │ 🖱 click (500, 300)  │   │  tại đây          │
│  │ ▸ Click │ │  └──────────────────────┘   │                   │
│  │ ▸ Key   │ │  ┌──────────────────────┐   │                   │
│  │ ▸ Type  │ │  │ ⏱ delay 500 ms      │   │                   │
│  ├─────────┤ │  └──────────────────────┘   │                   │
│  │Control  │ │  ┌──────────────────────┐   │                   │
│  │ ▸ If    │ │  │ ⬦ IF pixel=red       │   │                   │
│  │ ▸ Loop  │ │  │  ┌── THEN ─────────┐ │   │                   │
│  ├─────────┤ │  │  │ 🖱 click (600..) │ │   │                   │
│  │ Utils   │ │  │  └─────────────────┘ │   │                   │
│  │ ▸ Delay │ │  │  ┌── ELSE ─────────┐ │   │                   │
│  │ ▸ Var   │ │  │  │ 🖱 click (700..) │ │   │                   │
│  │ ▸ Call  │ │  │  └─────────────────┘ │   │                   │
│  └─────────┘ │  └──────────────────────┘   │                   │
│              │  ┌──────────────────────┐   │                   │
│              │  │ 🔁 LOOP 3 times      │   │                   │
│              │  │  ┌─────────────────┐ │   │                   │
│              │  │  │ ⌨ type "hello"  │ │   │                   │
│              │  │  └─────────────────┘ │   │                   │
│              │  └──────────────────────┘   │                   │
│              │  [+] Add block...           │                   │
└──────────────┴──────────────────────────────┴───────────────────┘
```

### 4.2 Màu sắc (Pastel — dễ thương, nhạt)

| Block Type    | Background     | Header Accent  | Icon |
|---------------|----------------|----------------|------|
| Action Click  | `#E3F2FF`      | `#64B5F6`      | 🖱   |
| Action Key    | `#E3F2FF`      | `#64B5F6`      | ⌨   |
| Action Type   | `#E3F2FF`      | `#64B5F6`      | 📝   |
| Action Scroll | `#E3F2FF`      | `#64B5F6`      | ↕   |
| Delay         | `#EDE7F6`      | `#B39DDB`      | ⏱   |
| Condition     | `#FFF3E0`      | `#FFCC80`      | 👁   |
| Branch (IF)   | `#E8F5E9`      | `#81C784`      | ⬦   |
| Loop          | `#FFFDE7`      | `#FFD54F`      | 🔁   |
| Set Variable  | `#FCE4EC`      | `#F48FB1`      | 📌   |
| Call Scenario | `#E0F7FA`      | `#80DEEA`      | 📂   |

Container nội bộ (THEN/ELSE/body):
- Background: `#FAFAFA` (trắng nhạt)
- Border: `2px dashed #CCCCCC`
- Khi hover drop zone: `2px dashed #64B5F6` + background `#EEF6FF`

### 4.3 Block anatomy

```
┌─[≡]─────────────────────────────────── [▼] [✏] [✕]─┐
│  🖱  click  ·  (500, 300)  ·  left button            │  ← Header (màu)
├──────────────────────────────────────────────────────┤
│  X: [500]  Y: [300]  Button: [left ▼]  [🎯 Pick]    │  ← Body (trắng, collapsed ẩn)
└──────────────────────────────────────────────────────┘
```

- `[≡]` = drag handle (6 chấm, kéo để reorder)
- `[▼]` = expand/collapse body
- `[✏]` = edit mode (mở inline fields)
- `[✕]` = delete block

---

## 5. Kiến trúc code mới

### 5.1 Cấu trúc thư mục

```
app/ui/block_editor/
├── __init__.py
├── block_editor_panel.py      # Panel chính, thay thế steps listbox
├── block_canvas.py            # Scroll area + danh sách block dọc
├── block_palette.py           # Panel trái: palette kéo thả
├── drop_indicator.py          # Widget chỉ vị trí sẽ drop
├── blocks/
│   ├── __init__.py
│   ├── base_block.py          # Base class, drag handle, header, collapse
│   ├── action_block.py        # ActionStep (click, key, type, scroll, move)
│   ├── delay_block.py         # DelayStep
│   ├── condition_block.py     # ConditionStep
│   ├── branch_block.py        # BranchStep (IF/THEN/ELSE containers)
│   ├── loop_block.py          # LoopStep (mới — loop N lần hoặc while)
│   ├── variable_block.py      # SetVariableStep
│   └── call_block.py          # CallScenarioStep
└── block_bridge.py            # Convert Block ↔ core Step models
```

### 5.2 Class relationships

```
BlockCanvas
  └── QScrollArea
        └── QWidget (container)
              ├── BlockWidget (base)
              │     ├── ActionBlock
              │     ├── DelayBlock
              │     ├── ConditionBlock
              │     ├── VariableBlock
              │     └── CallBlock
              └── ContainerBlock (base, có nested list)
                    ├── BranchBlock
                    │     ├── ThenContainer (BlockCanvas nhỏ)
                    │     └── ElseContainer (BlockCanvas nhỏ)
                    └── LoopBlock
                          └── BodyContainer (BlockCanvas nhỏ)
```

### 5.3 Drag & Drop protocol

Dùng Qt Drag & Drop:

1. **Drag start**: User kéo handle `[≡]` → `QDrag` mang `BlockMimeData` (type + index path)
2. **Drag over**: BlockCanvas/Container nhận `dragMoveEvent` → show `DropIndicator` (đường ngang màu xanh)
3. **Drop**: `dropEvent` → insert block vào vị trí mới, xóa khỏi vị trí cũ
4. **From palette**: Kéo block type từ palette → tạo block mới với giá trị default

```python
class BlockMimeData(QMimeData):
    def __init__(self, block: BaseBlock, source_container: BlockCanvas):
        self.block = block
        self.source = source_container
```

### 5.4 Block ↔ Model bridge

```python
# block_bridge.py
def block_to_step(block: BaseBlock) -> Step:
    """Convert UI block → core Step dataclass"""
    ...

def step_to_block(step: Step) -> BaseBlock:
    """Convert core Step dataclass → UI block widget"""
    ...

def canvas_to_steps(canvas: BlockCanvas) -> list[Step]:
    """Serialize toàn bộ canvas thành list[Step]"""
    ...

def steps_to_canvas(steps: list[Step], canvas: BlockCanvas) -> None:
    """Load list[Step] vào canvas"""
    ...
```

---

## 6. Loop Block (tính năng mới)

Hiện tại engine chưa có loop. Thêm vào cùng lúc với UI.

### 6.1 Model mới (models.py)

```python
@dataclass
class LoopStep:
    step_type: StepType = field(default=StepType.LOOP, init=False)
    count: int = 1                          # Số lần lặp (0 = vô hạn)
    body: list[Step] = field(default_factory=list)
```

### 6.2 Player (player.py)

```python
def _execute_loop(self, step: LoopStep) -> bool:
    iterations = step.count if step.count > 0 else float('inf')
    i = 0
    while i < iterations and not self._stop_event.is_set():
        ok = self._execute_steps(step.body, top_level=False)
        if not ok:
            return False
        i += 1
    return True
```

### 6.3 JSON format

```json
{
  "type": "loop",
  "count": 3,
  "body": [
    { "type": "click", "x": 500, "y": 300, "button": "left" }
  ]
}
```

---

## 7. Integration với hệ thống hiện tại

### 7.1 Recorder integration

Khi record xong, steps từ recorder → `steps_to_canvas()` → hiển thị dưới dạng blocks.
Không đổi gì ở recorder.

### 7.2 Player integration

Khi play, `canvas_to_steps()` → lấy `list[Step]` → player chạy như cũ.
Thêm: player gọi callback `on_step_start(index_path)` → canvas highlight block đang chạy (border xanh nhấp nháy).

### 7.3 Save/Load

```python
# Save: canvas → steps → serializer → JSON file (không đổi)
# Load: JSON file → deserializer → steps → canvas
```

Format JSON giữ nguyên 100%. Scenarios cũ load được bình thường.

### 7.4 Screen Picker

Block editor tái dùng `ScreenPickerOverlay` từ `app/ui/screen_picker.py` không đổi.

---

## 8. Kế hoạch triển khai

### Phase 6.1 — Foundation (3 ngày)

- [ ] Thêm PySide6 vào requirements.txt
- [ ] Tạo cấu trúc thư mục `app/ui/block_editor/`
- [ ] `BaseBlock`: header bar, drag handle, expand/collapse, delete, QSS styling
- [ ] `BlockCanvas`: scroll area, vertical layout, DropIndicator
- [ ] Drag & drop trong cùng một canvas (reorder)

**Deliverable**: Có thể kéo thả reorder Action blocks cơ bản.

---

### Phase 6.2 — Tất cả block types (4 ngày)

- [ ] `ActionBlock` (click, key_press, type_text, mouse_move, mouse_scroll)
- [ ] `DelayBlock` (min ms, max ms)
- [ ] `ConditionBlock` (pixel_color, image_match, ocr_text)
- [ ] `VariableBlock`
- [ ] `CallBlock`
- [ ] `BranchBlock` với THEN/ELSE containers lồng nhau
- [ ] `LoopBlock` với body container lồng nhau

**Deliverable**: Tất cả step types có block tương ứng, nested hiển thị đúng.

---

### Phase 6.3 — Palette (2 ngày)

- [ ] `BlockPalette`: grouped list bên trái
- [ ] Kéo từ palette → thêm block mới vào canvas
- [ ] Double-click block trong palette → thêm vào cuối list

**Deliverable**: Tạo block mới từ palette, không cần dialog.

---

### Phase 6.4 — Integration (3 ngày)

- [ ] `block_bridge.py`: `step_to_block`, `block_to_step`, `canvas_to_steps`, `steps_to_canvas`
- [ ] LoopStep: thêm vào `models.py`, `player.py`, `serializer.py`
- [ ] Kết nối recorder → canvas (new steps appear as blocks)
- [ ] Kết nối canvas → player (Save + Play)
- [ ] Load/Save JSON qua existing serializer
- [ ] Highlight block đang chạy khi play

**Deliverable**: Full workflow hoạt động end-to-end.

---

### Phase 6.5 — Polish (2 ngày)

- [ ] Undo/Redo (QUndoStack)
- [ ] Animation expand/collapse (QPropertyAnimation)
- [ ] Drag between containers (THEN ↔ ELSE ↔ Loop body)
- [ ] Context menu chuột phải (Duplicate, Move to THEN/ELSE)
- [ ] Empty state placeholder ("Drag blocks here or press Record")
- [ ] Tương thích Windows (High DPI scaling)

**Deliverable**: UI hoàn chỉnh, smooth, production-ready.

---

## 9. Files thay đổi

| File | Loại | Mô tả |
|------|------|-------|
| `requirements.txt` | Modified | Thêm `PySide6>=6.6.0` |
| `app/core/models.py` | Modified | Thêm `LoopStep`, `StepType.LOOP` |
| `app/core/player.py` | Modified | Thêm `_execute_loop()` |
| `app/core/serializer.py` | Modified | Serialize/deserialize `LoopStep` |
| `app/ui/block_editor/` | New dir | Toàn bộ block editor UI |
| `app/ui/block_editor/block_editor_panel.py` | New | Panel chính |
| `app/ui/block_editor/block_canvas.py` | New | Scroll area + danh sách |
| `app/ui/block_editor/block_palette.py` | New | Palette trái |
| `app/ui/block_editor/drop_indicator.py` | New | Drop line indicator |
| `app/ui/block_editor/blocks/base_block.py` | New | Base class |
| `app/ui/block_editor/blocks/action_block.py` | New | Action block |
| `app/ui/block_editor/blocks/delay_block.py` | New | Delay block |
| `app/ui/block_editor/blocks/condition_block.py` | New | Condition block |
| `app/ui/block_editor/blocks/branch_block.py` | New | IF/ELSE block |
| `app/ui/block_editor/blocks/loop_block.py` | New | Loop block |
| `app/ui/block_editor/blocks/variable_block.py` | New | Variable block |
| `app/ui/block_editor/blocks/call_block.py` | New | Call scenario block |
| `app/ui/block_editor/block_bridge.py` | New | Model ↔ Block bridge |
| `app/ui/main_window.py` | Modified | Swap listbox → block editor panel |

**Không thay đổi**: `recorder.py`, `scenario_engine.py`, `conditions.py`, `actions.py`, `screen_picker.py`, `add_step_dialog.py` (giữ lại cho fallback), `database.py`, `repository.py`

---

## 10. Rủi ro & Giải pháp

| Rủi ro | Giải pháp |
|--------|-----------|
| PySide6 + PyInstaller phức tạp | Test build sớm ở Phase 6.1, dùng `--collect-all PySide6` |
| Tkinter và PySide6 không chạy cùng process | Migrate hoàn toàn, không mix |
| Screen picker overlay (Tk) không còn | Port `ScreenPickerOverlay` sang PySide6 `QDialog` |
| JSON cũ không có `loop` | Serializer backward-compatible, field absence = no loop |
| High DPI trên Windows | `QApplication.setHighDpiScaleFactorRoundingPolicy()` |
