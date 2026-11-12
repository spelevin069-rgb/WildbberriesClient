import sys
from PyQt6.QtWidgets import QApplication
from src.ui.app import WildbberriesApp


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('WildbberriesClient')
    window = WildbberriesApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
