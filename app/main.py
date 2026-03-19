"""
Entry point for SkyjarBot.
"""
import tkinter as tk
from app.ui.main_window import MainWindow


def main() -> None:
    root = tk.Tk()
    app = MainWindow(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()


if __name__ == "__main__":
    main()
