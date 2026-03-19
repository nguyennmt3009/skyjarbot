"""
Block palette — left panel listing all draggable block types.
Drag a type from here to the canvas to create a new block.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QCursor

from app.ui.block_editor.blocks.base_block import PALETTE_MIME_TYPE

# (display_name, palette_type_key, bg_color, icon)
_PALETTE_ITEMS: list[tuple[str, str, str, str]] = [
    # Actions
    ("Click",        "action_click",   "#D0E8FF", "🖱"),
    ("Key Press",    "action_key",     "#DCF0FF", "⌨"),
    ("Type Text",    "action_type",    "#DCF0FF", "📝"),
    ("Mouse Move",   "action_move",    "#D0E8FF", "↔"),
    ("Scroll",       "action_scroll",  "#D0E8FF", "↕"),
    # Control flow
    ("IF / ELSE",    "branch",         "#D5EFDD", "⬦"),
    ("Loop",         "loop",           "#FFF5CC", "🔁"),
    # Utilities
    ("Delay",        "delay",          "#E8DEFF", "⏱"),
    ("Wait (Cond.)", "condition",      "#FFE8CC", "👁"),
    ("Set Variable", "variable",       "#FFD6E8", "📌"),
    ("Call Scenario","call",           "#D5F0F0", "📂"),
]

_GROUP_HEADERS = {
    "action_click":  ("ACTIONS",       "#5890C8"),
    "branch":        ("CONTROL FLOW",  "#3A9E5F"),
    "delay":         ("UTILITIES",     "#8060A0"),
}


class PaletteItem(QFrame):
    """Single draggable item in the palette."""

    def __init__(self, name: str, block_type: str, bg: str, icon: str, parent=None):
        super().__init__(parent)
        self._block_type = block_type
        self._drag_start = None

        self.setFixedHeight(34)
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 6px;
                border: 1px solid rgba(0,0,0,0.07);
            }}
            QFrame:hover {{
                border: 1px solid rgba(0,0,0,0.18);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        from PySide6.QtWidgets import QHBoxLayout
        h = QHBoxLayout()
        h.setSpacing(6)
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 13px;")
        h.addWidget(lbl_icon)
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: 600; color: rgba(0,0,0,0.65);")
        h.addWidget(lbl_name)
        h.addStretch()
        layout.addLayout(h)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.LeftButton) or self._drag_start is None:
            super().mouseMoveEvent(event)
            return
        from PySide6.QtWidgets import QApplication
        if (event.position().toPoint() - self._drag_start).manhattanLength() < QApplication.startDragDistance():
            return
        mime = QMimeData()
        mime.setData(PALETTE_MIME_TYPE, self._block_type.encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setHotSpot(self._drag_start)
        drag.exec(Qt.CopyAction)


class BlockPalette(QWidget):
    """Left panel: grouped, draggable list of all block types."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(160)
        self.setStyleSheet("background: #F0F4FB;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("  Blocks")
        title.setFixedHeight(36)
        title.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 700;
                color: rgba(0,0,0,0.5);
                letter-spacing: 1px;
                background: #E4EAFF;
                border-bottom: 1px solid #D0DAF5;
            }
        """)
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #F0F4FB; }")

        container = QWidget()
        container.setStyleSheet("background: #F0F4FB;")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(4)

        current_group = None
        for name, btype, bg, icon in _PALETTE_ITEMS:
            if btype in _GROUP_HEADERS:
                grp_text, grp_color = _GROUP_HEADERS[btype]
                lbl = QLabel(grp_text)
                lbl.setStyleSheet(f"""
                    QLabel {{
                        font-size: 9px;
                        font-weight: 700;
                        color: {grp_color};
                        letter-spacing: 1.2px;
                        padding-top: 8px;
                    }}
                """)
                vbox.addWidget(lbl)

            item = PaletteItem(name, btype, bg, icon)
            vbox.addWidget(item)

        vbox.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)
