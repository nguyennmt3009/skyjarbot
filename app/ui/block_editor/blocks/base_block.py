"""
Base class for all step blocks in the visual editor.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, Signal, QPoint, QMimeData
from PySide6.QtGui import QDrag, QColor, QCursor

if TYPE_CHECKING:
    from app.ui.block_editor.block_canvas import BlockCanvas

DRAG_MIME_TYPE = "application/x-skyjar-block"
PALETTE_MIME_TYPE = "application/x-skyjar-palette"


class BlockMimeData(QMimeData):
    """MIME data carrying an actual block widget reference for intra-canvas moves."""
    def __init__(self, block: "BaseBlock", source_canvas: "BlockCanvas"):
        super().__init__()
        self.block = block
        self.source_canvas = source_canvas
        self.setData(DRAG_MIME_TYPE, b"1")


class DragHandle(QLabel):
    """The ⠿ grip that initiates drag-and-drop reordering."""

    def __init__(self, block: "BaseBlock"):
        super().__init__(":::")
        self._block = block
        self._drag_start: Optional[QPoint] = None
        self.setFixedWidth(22)
        self.setCursor(QCursor(Qt.SizeAllCursor))
        self.setStyleSheet("color: rgba(0,0,0,0.28); font-size: 10px; letter-spacing: -1px; padding: 0 2px;")
        self.setToolTip("Drag to reorder")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self._drag_start is None:
            super().mouseMoveEvent(event)
            return
        delta = event.position().toPoint() - self._drag_start
        if delta.manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        canvas = self._block._canvas
        if canvas is None:
            return

        mime = BlockMimeData(self._block, canvas)
        drag = QDrag(self)
        drag.setMimeData(mime)

        # Ghost pixmap — snapshot of the block header only
        pixmap = self._block.grab()
        drag.setPixmap(pixmap.scaledToWidth(min(pixmap.width(), 380)))
        drag.setHotSpot(QPoint(20, 10))
        drag.exec(Qt.MoveAction)


# ── Block header ──────────────────────────────────────────────────────────────

class BlockHeader(QFrame):
    """Colored top bar: drag handle | icon | type label | description | ▾ | ✕"""

    def __init__(self, bg_color: str, icon: str, type_label: str, parent=None):
        super().__init__(parent)
        self._bg = bg_color
        self.setFixedHeight(36)
        self._apply_style(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 8, 0)
        layout.setSpacing(5)

        self._drag_handle: Optional[DragHandle] = None  # set by BaseBlock

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(self._icon_lbl)

        type_lbl = QLabel(type_label)
        type_lbl.setStyleSheet(
            "font-weight: 700; font-size: 11px; color: rgba(0,0,0,0.65); letter-spacing: 0.3px;"
        )
        layout.addWidget(type_lbl)

        self._desc_lbl = QLabel("")
        self._desc_lbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.50);")
        self._desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._desc_lbl.setWordWrap(False)
        layout.addWidget(self._desc_lbl)

        self.expand_btn = QPushButton("v")
        self.expand_btn.setFixedSize(22, 22)
        self.expand_btn.setStyleSheet(_icon_btn_style())
        layout.addWidget(self.expand_btn)

        self.delete_btn = QPushButton("x")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setStyleSheet(_icon_btn_style(danger=True))
        layout.addWidget(self.delete_btn)

    def set_description(self, text: str) -> None:
        self._desc_lbl.setText(f"  ·  {text}" if text else "")

    def set_highlighted(self, on: bool) -> None:
        self._apply_style(on)

    def _apply_style(self, highlighted: bool) -> None:
        if highlighted:
            c = QColor(self._bg).darker(115).name()
        else:
            c = self._bg
        self.setStyleSheet(f"""
            QFrame {{
                background: {c};
                border-radius: 8px 8px 0 0;
                border: none;
            }}
        """)


# ── Base block ────────────────────────────────────────────────────────────────

class BaseBlock(QWidget):
    """Base class for every step block widget."""

    delete_requested = Signal(object)   # emits self
    changed = Signal()                  # emits when any field changes

    HEADER_COLOR = "#E0E0E0"
    ICON = "●"
    TYPE_LABEL = "Block"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._canvas: Optional["BlockCanvas"] = None
        self._expanded = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 4)
        outer.setSpacing(0)

        # ── Header
        self._header = BlockHeader(self.HEADER_COLOR, self.ICON, self.TYPE_LABEL)
        self._header.expand_btn.clicked.connect(self._toggle_expand)
        self._header.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        outer.addWidget(self._header)

        # Insert drag handle at index 0 of header layout
        handle = DragHandle(self)
        self._header._drag_handle = handle
        self._header.layout().insertWidget(0, handle)

        # ── Body
        self._body = QFrame()
        self._body.setStyleSheet("""
            QFrame {
                background: #F8F9FE;
                border: 1px solid #DDEAFF;
                border-top: none;
                border-radius: 0 0 8px 8px;
            }
        """)
        self._body.setMinimumHeight(40)
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(12, 10, 12, 10)
        body_layout.setSpacing(7)
        self._build_body(body_layout)
        outer.addWidget(self._body)
        # Start collapsed: body hidden, expand button points right
        self._body.hide()
        self._header.expand_btn.setText(">")

        # Left accent border (colored strip)
        self.setStyleSheet(f"""
            BaseBlock {{
                border-left: 3px solid {QColor(self.HEADER_COLOR).darker(130).name()};
                border-radius: 8px;
            }}
        """)

    # ── Override in subclasses ────────────────────────────────────────────────

    def _build_body(self, layout: QVBoxLayout) -> None:
        """Add form widgets to the body layout."""

    def get_description(self) -> str:
        """One-liner shown in the collapsed header."""
        return ""

    def to_step(self):
        """Convert this block to a core Step dataclass."""
        raise NotImplementedError

    def from_step(self, step) -> None:
        """Populate form fields from a core Step dataclass."""

    # ── Public API ────────────────────────────────────────────────────────────

    def update_description(self) -> None:
        self._header.set_description(self.get_description())

    def set_canvas(self, canvas: "BlockCanvas") -> None:
        self._canvas = canvas

    def set_highlighted(self, on: bool) -> None:
        self._header.set_highlighted(on)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _toggle_expand(self) -> None:
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        self._header.expand_btn.setText("v" if self._expanded else ">")
        # Notify canvas to update scroll height
        if self._canvas is not None:
            self._canvas._sync_size()


# ── QSS helpers ───────────────────────────────────────────────────────────────

def _icon_btn_style(danger: bool = False) -> str:
    hover_bg = "rgba(220,50,50,0.12)" if danger else "rgba(0,0,0,0.07)"
    hover_color = "#c0392b" if danger else "rgba(0,0,0,0.75)"
    return f"""
        QPushButton {{
            border: none;
            background: transparent;
            font-size: 11px;
            color: rgba(0,0,0,0.38);
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background: {hover_bg};
            color: {hover_color};
        }}
    """


def form_row(label_text: str, widget: QWidget, label_width: int = 70) -> QHBoxLayout:
    """Return a horizontal label + widget row for block body forms."""
    row = QHBoxLayout()
    row.setSpacing(6)
    lbl = QLabel(label_text)
    lbl.setFixedWidth(label_width)
    lbl.setStyleSheet("font-size: 11px; color: rgba(0,0,0,0.55);")
    row.addWidget(lbl)
    row.addWidget(widget)
    return row


def style_input(widget: QWidget) -> QWidget:
    """Apply consistent form field styling and return the widget."""
    widget.setStyleSheet("""
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background: white;
            border: 1px solid #D8D8D8;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            color: #333;
        }
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #64B5F6;
        }
        QComboBox::drop-down { border: none; }
        QComboBox::down-arrow { image: none; width: 0; }
    """)
    return widget


def pick_btn() -> QPushButton:
    """Small 🎯 coordinate picker button."""
    btn = QPushButton("🎯")
    btn.setFixedSize(26, 26)
    btn.setToolTip("Pick from screen")
    btn.setStyleSheet("""
        QPushButton {
            background: #EEF6FF;
            border: 1px solid #C9DEF6;
            border-radius: 5px;
            font-size: 13px;
        }
        QPushButton:hover { background: #D6EAFF; }
    """)
    return btn
