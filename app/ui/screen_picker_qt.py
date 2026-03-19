"""
PySide6 fullscreen screen picker.
Replaces the Tkinter ScreenPickerOverlay for the new Qt UI.

Usage:
    picker = ScreenPickerQt(mode="point")   # or "region"
    if picker.exec():
        print(picker.result_point)          # (x, y)
        print(picker.result_region)         # (x, y, w, h) or None
"""
from __future__ import annotations
from typing import Optional, Tuple

from PySide6.QtWidgets import QDialog, QApplication, QLabel
from PySide6.QtCore import Qt, QRect, QPoint, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QCursor


class ScreenPickerQt(QDialog):
    """
    Full-screen overlay for picking a screen coordinate or region.

    - Click            → returns point
    - Click + drag     → returns region (if mode="region")
    - ESC              → cancel (result is rejected)
    """

    def __init__(self, mode: str = "point", parent=None):
        super().__init__(parent)
        assert mode in ("point", "region"), "mode must be 'point' or 'region'"
        self._mode = mode

        self._start: Optional[QPoint] = None
        self._current: Optional[QPoint] = None
        self._dragging = False

        self.result_point: Optional[Tuple[int, int]] = None
        self.result_region: Optional[Tuple[int, int, int, int]] = None

        # Capture screenshot BEFORE window is shown
        screen = QApplication.primaryScreen()
        self._screenshot = screen.grabWindow(0)
        self._screen_geo = screen.geometry()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setGeometry(self._screen_geo)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Draw screenshot
        painter.drawPixmap(0, 0, self._screenshot)

        # Dark overlay
        if self._start and self._current and self._dragging:
            sel = QRect(self._start, self._current).normalized()
            # Overlay everywhere EXCEPT the selection
            painter.save()
            from PySide6.QtGui import QRegion
            outside = QRegion(self.rect()) - QRegion(sel)
            painter.setClipRegion(outside)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 110))
            painter.restore()
            # Selection border
            pen = QPen(QColor("#00d4ff"), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(sel)
            # Size label
            w, h = sel.width(), sel.height()
            label = f"{sel.x()},{sel.y()}  {w}×{h}"
            self._draw_label(painter, self._current, label)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 110))
            # Coordinate hint
            if self._current:
                label = f"{self._current.x()}, {self._current.y()}"
                self._draw_label(painter, self._current, label)

    def _draw_label(self, painter: QPainter, pos: QPoint, text: str) -> None:
        font = QFont("Consolas", 10)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        padding = 5
        rx = pos.x() + 14
        ry = pos.y() - th - padding * 2 - 4
        if rx + tw + padding * 2 > self.width():
            rx = pos.x() - tw - padding * 2 - 14
        if ry < 0:
            ry = pos.y() + 14
        painter.fillRect(rx - padding, ry - padding, tw + padding * 2, th + padding * 2,
                         QColor(0, 0, 0, 170))
        painter.setPen(QColor("#00d4ff"))
        painter.drawText(rx, ry + th - 2, text)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._start = event.position().toPoint()
            self._current = self._start
            self._dragging = False
            self.update()

    def mouseMoveEvent(self, event) -> None:
        self._current = event.position().toPoint()
        if self._start:
            delta = self._current - self._start
            if delta.manhattanLength() > 4:
                self._dragging = True
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self._start is None:
            return
        end = event.position().toPoint()

        if self._dragging and self._mode == "region":
            rect = QRect(self._start, end).normalized()
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            self.result_region = (x, y, w, h)
            self.result_point = (x, y)
        else:
            self.result_point = (self._start.x(), self._start.y())

        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject()
