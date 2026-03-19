"""
Entry point for SkyjarBot.
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.ui.main_window_qt import MainWindowQt


def main() -> None:
    # High-DPI support on Windows
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("SkyjarBot")
    window = MainWindowQt()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
