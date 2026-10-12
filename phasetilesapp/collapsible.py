"""Foldable dock sections and a scrolling wrapper.

A dock's content sets the window's minimum height; the setup dock and
both domain views stacked were taller than a 13-inch laptop screen,
so the window opened off the bottom of the display.  Scrolling makes
the minimum a few rows; folding lets the user keep what they use.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class Section(QWidget):
    def __init__(self, title, parent=None, expanded=True):
        super().__init__(parent)
        self.toggle = QToolButton()
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(expanded)
        self.toggle.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setSizePolicy(QSizePolicy.Policy.Expanding,
                                  QSizePolicy.Policy.Fixed)
        self.toggle.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; }")
        self.body = QFrame()
        self.body.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        v.addWidget(self.toggle)
        v.addWidget(self.body)
        self.toggle.toggled.connect(self._show)
        self._show(expanded)

    def title(self):
        return self.toggle.text()

    def _show(self, on):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if on
                                 else Qt.ArrowType.RightArrow)
        self.body.setVisible(on)


def scrolling(widget):
    """widget in a vertical-only scroll area, for a dock."""
    s = QScrollArea()
    s.setWidget(widget)
    s.setWidgetResizable(True)
    s.setFrameShape(QFrame.Shape.NoFrame)
    s.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    # with no horizontal bar, the dock must be wide enough for the
    # widest row plus the vertical bar, or that row is cut off
    s.setMinimumWidth(widget.minimumSizeHint().width()
                      + s.verticalScrollBar().sizeHint().width() + 2)
    return s


def fixed_dock(dock):
    """Movable and floatable, never closable: there is no menu entry
    to bring a closed dock back, so closing one lost it until the
    settings were reset."""
    F = dock.DockWidgetFeature
    dock.setFeatures(F.DockWidgetMovable | F.DockWidgetFloatable)
