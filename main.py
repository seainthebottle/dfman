import sys
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())
