"""
BlockCanvas — vertical list of blocks with drag-and-drop reordering.
Both the main editor and nested containers (branch/loop) use this widget.

Sizing contract:
  - Horizontal: Expanding  → fills the QScrollArea viewport width.
  - Vertical:   Minimum    → never shrinks below content; QScrollArea scrolls
                             when content exceeds viewport.
  - minimumSizeHint() is overridden to return the actual content height so that
    QScrollArea(widgetResizable=True) never squashes blocks.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QPen, QColor

from app.ui.block_editor.blocks.base_block import (
    BaseBlock, BlockMimeData, DRAG_MIME_TYPE, PALETTE_MIME_TYPE,
)

if TYPE_CHECKING:
    from app.core.models import Step


class BlockCanvas(QWidget):
    """Vertical ordered list of BaseBlock widgets with drag-and-drop."""

    blocks_changed = Signal()

    def __init__(self, parent=None, compact: bool = False):
        super().__init__(parent)
        self._compact = compact
        self._blocks: list[BaseBlock] = []
        self._drop_y: Optional[int] = None

        self.setAcceptDrops(True)
        # Expanding: fill width.  Minimum: size to content, never compress.
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        bg = "#F0F4FB" if not compact else "#F7F9FC"
        self.setStyleSheet(f"background: {bg};")

        self._layout = QVBoxLayout(self)
        pad = 6 if compact else 10
        self._layout.setContentsMargins(pad, pad, pad, pad)
        self._layout.setSpacing(5)
        self._layout.setAlignment(Qt.AlignTop)

        self._empty_label = _make_empty_label()
        self._layout.addWidget(self._empty_label)

        # Floor so the canvas is never invisible
        self._floor = 64 if compact else 200
        self.setMinimumHeight(self._floor)

    # ── Qt sizing overrides ───────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(self._layout.sizeHint().width(),
                     max(self._content_height(), self._floor))

    def minimumSizeHint(self) -> QSize:
        # QScrollArea(widgetResizable=True) queries minimumSizeHint to decide
        # the minimum widget height.  Return content height so it never
        # compresses the canvas to viewport height.
        return QSize(200, max(self._content_height(), self._floor))

    def _content_height(self) -> int:
        """Sum of block heights + spacing + margins."""
        m = self._layout.contentsMargins()
        h = m.top() + m.bottom()
        sp = self._layout.spacing()
        for i, b in enumerate(self._blocks):
            h += b.sizeHint().height()
            if i > 0:
                h += sp
        if not self._blocks:
            h += self._empty_label.minimumHeight()
        return h

    # ── Block management ──────────────────────────────────────────────────────

    def add_block(self, block: BaseBlock) -> None:
        self._insert_at(len(self._blocks), block)

    def insert_block(self, index: int, block: BaseBlock) -> None:
        self._insert_at(index, block)

    def remove_block(self, block: BaseBlock) -> None:
        if block not in self._blocks:
            return
        self._blocks.remove(block)
        self._layout.removeWidget(block)
        block.setParent(None)
        self._refresh_empty()
        self.blocks_changed.emit()
        self._sync_size()

    def get_blocks(self) -> list[BaseBlock]:
        return list(self._blocks)

    def clear(self) -> None:
        for b in list(self._blocks):
            self.remove_block(b)

    def get_steps(self) -> list[Step]:
        steps = []
        for b in self._blocks:
            try:
                steps.append(b.to_step())
            except Exception:
                pass
        return steps

    def load_steps(self, steps: list[Step]) -> None:
        from app.ui.block_editor.block_bridge import step_to_block
        self.clear()
        for step in steps:
            block = step_to_block(step)
            if block:
                self.add_block(block)

    # ── Drag & drop ───────────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if (event.mimeData().hasFormat(DRAG_MIME_TYPE)
                or event.mimeData().hasFormat(PALETTE_MIME_TYPE)):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if (event.mimeData().hasFormat(DRAG_MIME_TYPE)
                or event.mimeData().hasFormat(PALETTE_MIME_TYPE)):
            y = int(event.position().y())
            self._drop_y = self._indicator_y(self._get_drop_index(y))
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._drop_y = None
        self.update()

    def dropEvent(self, event) -> None:
        self._drop_y = None
        self.update()

        y = int(event.position().y())
        target_idx = self._get_drop_index(y)
        mime = event.mimeData()

        if mime.hasFormat(DRAG_MIME_TYPE) and isinstance(mime, BlockMimeData):
            block: BaseBlock = mime.block
            src_canvas: BlockCanvas = mime.source_canvas
            if src_canvas is self:
                src_idx = self._blocks.index(block) if block in self._blocks else -1
                if src_idx != -1 and src_idx < target_idx:
                    target_idx -= 1
            src_canvas.remove_block(block)
            self._insert_at(target_idx, block)
            event.acceptProposedAction()

        elif mime.hasFormat(PALETTE_MIME_TYPE):
            block_type = bytes(mime.data(PALETTE_MIME_TYPE)).decode()
            block = _create_block_by_type(block_type)
            if block:
                self._insert_at(target_idx, block)
            event.acceptProposedAction()

        else:
            event.ignore()

    # ── Drop indicator ────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._drop_y is not None:
            painter = QPainter(self)
            pen = QPen(QColor("#64B5F6"), 3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            m = self._layout.contentsMargins()
            painter.drawLine(m.left() + 4, self._drop_y,
                             self.width() - m.right() - 4, self._drop_y)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _insert_at(self, index: int, block: BaseBlock) -> None:
        index = max(0, min(index, len(self._blocks)))
        block.set_canvas(self)
        block.delete_requested.connect(self.remove_block)
        block.changed.connect(self.blocks_changed)

        self._blocks.insert(index, block)
        self._layout.insertWidget(index, block)
        block.show()   # ensures sizeHint() is computed before _sync_size

        self._refresh_empty()
        self.blocks_changed.emit()
        self._sync_size()

    def _sync_size(self) -> None:
        """Update minimumHeight so QScrollArea never squashes us."""
        h = max(self._content_height(), self._floor)
        self.setMinimumHeight(h)
        self.updateGeometry()

    def _refresh_empty(self) -> None:
        self._empty_label.setVisible(len(self._blocks) == 0)

    def _get_drop_index(self, y: int) -> int:
        for i, block in enumerate(self._blocks):
            if y < block.y() + block.height() // 2:
                return i
        return len(self._blocks)

    def _indicator_y(self, index: int) -> int:
        m = self._layout.contentsMargins()
        if not self._blocks:
            return m.top()
        if index == 0:
            return self._blocks[0].y() - 3
        if index >= len(self._blocks):
            last = self._blocks[-1]
            return last.y() + last.height() + 1
        return self._blocks[index].y() - 3


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_empty_label() -> QLabel:
    lbl = QLabel("Drop blocks here  /  press Record")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setMinimumHeight(60)
    lbl.setStyleSheet("""
        QLabel {
            color: #BBCCE0;
            font-size: 11px;
            font-style: italic;
            border: 2px dashed #D8E6F5;
            border-radius: 6px;
            padding: 12px;
        }
    """)
    return lbl


def _create_block_by_type(block_type: str) -> Optional[BaseBlock]:
    from app.ui.block_editor.blocks.action_block import ActionBlock
    from app.ui.block_editor.blocks.delay_block import DelayBlock
    from app.ui.block_editor.blocks.condition_block import ConditionBlock
    from app.ui.block_editor.blocks.branch_block import BranchBlock
    from app.ui.block_editor.blocks.loop_block import LoopBlock
    from app.ui.block_editor.blocks.variable_block import VariableBlock
    from app.ui.block_editor.blocks.call_block import CallBlock

    mapping = {
        "action_click":  lambda: ActionBlock("click"),
        "action_key":    lambda: ActionBlock("key_press"),
        "action_type":   lambda: ActionBlock("type_text"),
        "action_move":   lambda: ActionBlock("mouse_move"),
        "action_scroll": lambda: ActionBlock("mouse_scroll"),
        "delay":         DelayBlock,
        "condition":     ConditionBlock,
        "branch":        BranchBlock,
        "loop":          LoopBlock,
        "variable":      VariableBlock,
        "call":          CallBlock,
    }
    factory = mapping.get(block_type)
    return factory() if factory else None
