# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    setup_logging()
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle('Fusion')
    dark_palette = get_dark_palette()
    app.setPalette(dark_palette)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    return app.exec_()

def get_dark_palette():
    from PyQt5.QtGui import QPalette, QColor
    from PyQt5.QtCore import Qt
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    return palette

if __name__ == "__main__":
    sys.exit(main())