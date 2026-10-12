"""Preferences: MC workers, an optional full RCSR file, and the tile
cache.  Not undoable -- they are not part of a diagram -- and applied
at once."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

from phasetiles import nets


def _size(b):
    return f"{b / 1e3:.0f} kB" if b < 1e6 else f"{b / 1e6:.1f} MB"


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
        # the cache is never pruned on its own; this is the way out
        self.cache_info = QLabel()
        self.clear_cache = QPushButton("Clear Cache…")
        self.clear_cache.clicked.connect(self._clear_cache)
        # deleting tiles under a run would lose the ones it is writing
        self.clear_cache.setEnabled(not getattr(parent, "running",
                                                False))
        row = QHBoxLayout()
        row.addWidget(self.cache_info, 1)
        row.addWidget(self.clear_cache)
        f.addRow("Tile cache", row)
        self._show_cache()
        self.error = QLabel()
        f.addRow(self.error)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        f.addRow(bb)

    def _show_cache(self):
        n, size = self.doc.store.usage()
        self.cache_info.setText(f"{n} tiles · {_size(size)}")
        self.cache_info.setToolTip(str(self.doc.store.root))

    def _clear_cache(self):
        n, size = self.doc.store.usage()
        r = QMessageBox.question(
            self, "Clear Cache",
            f"Delete all {n} computed tiles ({_size(size)})?\n"
            "Every diagram will need to be run again; saved .phtiles "
            "files keep their own tiles.")
        if r != QMessageBox.StandardButton.Yes:
            return
        from phasetilesapp import diagram_painter
        self.doc.store.clear()
        diagram_painter.forget()
        self.doc.notify_tiles()
        self._show_cache()

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
        old = self.settings.rcsr_path
        nets.set_source(path)
        try:
            names = nets.list_2d()
        except Exception as e:          # unparsable file
            names, why = {}, f"{path} could not be read ({e})."
        else:
            why = (f"{path or 'The shipped file'} has no net "
                   f"'{self.doc.spec.net}', which the open diagram "
                   "uses; open another diagram first.")
        if self.doc.spec.net not in names:
            nets.set_source(old)
            self.error.setText(why)
            return False
        self.settings.workers = self.workers.value()
        self.settings.rcsr_path = path
        self.doc._net = None
        self.doc.specChanged.emit(self.doc.spec, self.doc.spec)
        return True

    def _ok(self):
        if self.apply():
            self.accept()
