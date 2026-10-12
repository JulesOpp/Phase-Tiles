"""Preferences: MC workers and an optional full RCSR file.  Not
undoable -- they are not part of a diagram -- and applied at once."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from phasetiles import nets


class PreferencesDialog(QDialog):
    def __init__(self, settings, doc, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.settings, self.doc = settings, doc
        f = QFormLayout(self)
        self.workers = QSpinBox()
        self.workers.setRange(1, 8)
        self.workers.setValue(settings.workers)
        f.addRow("MC workers (2 suits 16 GB)", self.workers)
        self.rcsr = QLineEdit(settings.rcsr_path or "")
        self.rcsr.setPlaceholderText("shipped 2D extract")
        browse, reset = QPushButton("Browse…"), QPushButton("Reset")
        browse.clicked.connect(self._browse)
        reset.clicked.connect(lambda: self.rcsr.setText(""))
        row = QHBoxLayout()
        for w in (self.rcsr, browse, reset):
            row.addWidget(w)
        f.addRow("RCSR file", row)
        self.error = QLabel()
        f.addRow(self.error)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        f.addRow(bb)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "RCSR file", "", "RCSR (*.cgd)")
        if p:
            self.rcsr.setText(p)

    def apply(self):
        """Returns False (and says why) for a path that is not a file,
        so a typo cannot leave the app with no nets."""
        path = self.rcsr.text().strip() or None
        if path and not Path(path).is_file():
            self.error.setText(f"{path} is not a file.")
            return False
        self.settings.workers = self.workers.value()
        self.settings.rcsr_path = path
        nets.set_source(path)
        self.doc._net = None
        self.doc.specChanged.emit(self.doc.spec, self.doc.spec)
        return True

    def _ok(self):
        if self.apply():
            self.accept()
