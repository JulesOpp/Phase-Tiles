"""QApplication setup shared by the GUI, --selftest and --render."""
import sys

from PySide6.QtWidgets import QApplication


def app():
    a = QApplication.instance() or QApplication(sys.argv[:1])
    a.setOrganizationName("PhaseTiles")
    a.setApplicationName("Phase Tiles")
    return a
