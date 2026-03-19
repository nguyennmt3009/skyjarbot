"""
BlockEditorPanel — the main visual editor panel.
Contains: palette (left) + scrollable block canvas (center).
"""
from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QScrollArea, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, Signal

from app.ui.block_editor.block_canvas import BlockCanvas
from app.ui.block_editor.block_palette import BlockPalette
from app.core.models import Step


class BlockEditorPanel(QWidget):
    """The complete block editor: palette + scrollable canvas."""

    blocks_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left: palette
        self._palette = BlockPalette()
        layout.addWidget(self._palette)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #D8E0EF;")
        layout.addWidget(sep)

        # Center: scrollable block canvas
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #F0F4FB;
            }
            QScrollBar:vertical {
                background: #EAF0FA;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C0CFEA;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #A0B8DA; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._canvas = BlockCanvas()
        self._canvas.blocks_changed.connect(self.blocks_changed)
        self._scroll.setWidget(self._canvas)
        layout.addWidget(self._scroll, 1)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_steps(self, steps: list[Step]) -> None:
        """Load a list of Steps into the canvas."""
        self._canvas.load_steps(steps)

    def get_steps(self) -> list[Step]:
        """Serialize all blocks → list of Step objects."""
        return self._canvas.get_steps()

    def clear(self) -> None:
        self._canvas.clear()

    def add_step(self, step: Step) -> None:
        """Append one step (e.g. from recorder)."""
        from app.ui.block_editor.block_bridge import step_to_block
        block = step_to_block(step)
        if block:
            self._canvas.add_block(block)
            # Scroll to the new block
            self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            )

    def highlight_step(self, index: int, on: bool) -> None:
        """Highlight a block at the given top-level index (during playback)."""
        blocks = self._canvas.get_blocks()
        if 0 <= index < len(blocks):
            blocks[index].set_highlighted(on)
            if on:
                self._scroll.ensureWidgetVisible(blocks[index])
