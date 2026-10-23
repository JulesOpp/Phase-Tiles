"""The shell: menus, docks, status.  No physics here -- every action
asks the Document or the core."""
import dataclasses
import sys
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressBar,
)

from phasetilesapp.document import Document
from phasetilesapp.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self, document=None, make_domain_view=None):
        super().__init__()
        self.settings = Settings()
        source_note = self._apply_rcsr_source()
        self.doc = document or Document(
            store_root=self.settings.cache_root)
        self._make_domain_view = make_domain_view
        self.setWindowTitle("Phase Tiles")
        self._build_actions()
        self._build_menus()
        from phasetilesapp.diagram_view import DiagramView
        self.diagram = DiagramView(self.doc)
        self.setCentralWidget(self.diagram)
        from phasetilesapp.setup_dock import SetupDock
        self.setup = SetupDock(self.doc, self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,
                           self.setup)
        from phasetilesapp.domains_panel import DomainsPanel
        self.domains = DomainsPanel(self.doc, self._make_domain_view,
                                    self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,
                           self.domains)
        self.running = False
        self.runner = None
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(240)
        self.progress.hide()
        self.statusBar().addPermanentWidget(self.progress)
        self.doc.specChanged.connect(self._refresh)
        self.doc.modifiedChanged.connect(self._refresh)
        self._refresh()
        self._fit_screen()
        if source_note:
            self.statusBar().showMessage(source_note)

    def _fit_screen(self):
        """1240 x 860 where it fits, else the available screen less a
        margin, centred: a fixed 860 put the status bar below a
        13-inch laptop's dock, and 1400 wide ran off its right edge."""
        avail = self.screen().availableGeometry()
        self.resize(min(1240, avail.width() - 80),
                    min(860, avail.height() - 40))
        # docks at full width if the diagram keeps its minimum
        docks = (self.setup, self.domains)
        full = [d.widget().full_width for d in docks]
        room = self.width() - self.diagram.minimumWidth() - 24
        if sum(full) > room:
            k = max(room, 1) / sum(full)
            full = [max(d.widget().minimumWidth(), int(f * k))
                    for d, f in zip(docks, full, strict=True)]
        self.resizeDocks(list(docks), full, Qt.Orientation.Horizontal)
        fr = self.frameGeometry()
        fr.moveCenter(avail.center())
        self.move(fr.topLeft())

    def _apply_rcsr_source(self):
        """Before the Document exists, so its net comes from the
        user's file.  A file that has gone missing must not stop the
        app opening: fall back to the shipped extract and say so."""
        from pathlib import Path

        from phasetiles import nets
        path = self.settings.rcsr_path
        if path and not Path(path).is_file():
            nets.set_source(None)
            return (f"RCSR file {path} not found; using the shipped "
                    "nets (Preferences to change).")
        nets.set_source(path)
        return None

    def _act(self, text, slot, shortcut=None, checkable=False):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.setCheckable(checkable)
        a.triggered.connect(slot)
        return a

    def _build_actions(self):
        S = QKeySequence.StandardKey
        self.act_new = self._act("&New", self.new_diagram, S.New)
        self.act_open = self._act("&Open…", self.open_dialog, S.Open)
        self.act_save = self._act("&Save", self.save, S.Save)
        self.act_save_as = self._act("Save &As…", self.save_as_dialog,
                                     S.SaveAs)
        self.act_export = self._act("Export Image…",
                                    self.export_dialog, "Ctrl+E")
        self.act_prefs = self._act("Preferences…", self.preferences,
                                   S.Preferences)
        self.act_quit = self._act("&Quit", self.close, S.Quit)
        self.act_undo = self._act("&Undo", self.doc.undo, S.Undo)
        self.act_redo = self._act("&Redo", self.doc.redo, S.Redo)
        self.act_run = self._act("&Run", self.run, "Ctrl+R")
        self.act_stop = self._act("&Stop", self.stop, "Ctrl+.")
        self.act_centre_gamma = self._act(
            "Tiles Centred on Γ (0, 0)",
            lambda: self._set_centre("gamma"), checkable=True)
        self.act_centre_half = self._act(
            "Tiles Centred on (½, ½)",
            lambda: self._set_centre("half"), checkable=True)
        g = QActionGroup(self)
        g.addAction(self.act_centre_gamma)
        g.addAction(self.act_centre_half)
        self.act_show_t0 = self._act("Show T = 0 Lines",
                                     self._toggle_t0, checkable=True)

    def _build_menus(self):
        mb = self.menuBar()
        self.menu_file = mb.addMenu("&File")
        for a in (self.act_new, self.act_open, self.act_save,
                  self.act_save_as, None, self.act_export, None,
                  self.act_prefs, self.act_quit):
            if a is None:
                self.menu_file.addSeparator()
            else:
                self.menu_file.addAction(a)
        self.menu_edit = mb.addMenu("&Edit")
        self.menu_edit.addAction(self.act_undo)
        self.menu_edit.addAction(self.act_redo)
        self.menu_run = mb.addMenu("&Run")
        self.menu_run.addAction(self.act_run)
        self.menu_run.addAction(self.act_stop)
        self.menu_view = mb.addMenu("&View")
        sub = self.menu_view.addMenu("Tile Centre")
        sub.addAction(self.act_centre_gamma)
        sub.addAction(self.act_centre_half)
        self.menu_view.addAction(self.act_show_t0)
        self.menu_help = mb.addMenu("&Help")
        self.menu_help.addAction(self._act("About Phase Tiles",
                                           self.about))

    def _refresh(self, *_):
        st, d = self.doc.stack, self.doc.spec.display
        self.act_undo.setEnabled(st.can_undo)
        self.act_undo.setText("&Undo " + st.undo_text)
        self.act_redo.setEnabled(st.can_redo)
        self.act_redo.setText("&Redo " + st.redo_text)
        self.act_run.setEnabled(self.setup.ok and not self.running)
        self.act_stop.setEnabled(self.running)
        self.act_centre_gamma.setChecked(d.centre == "gamma")
        self.act_centre_half.setChecked(d.centre == "half")
        self.act_show_t0.setChecked(d.show_t0)
        name = self.doc.path.name if self.doc.path else "Untitled"
        self.setWindowTitle(f"{name}{' •' if self.doc.modified else ''}"
                            " — Phase Tiles")

    def _set_display(self, text, **kw):
        s = self.doc.spec
        self.doc.set_spec(
            s.replace(display=dataclasses.replace(s.display, **kw)),
            text)

    def _set_centre(self, c):
        self._set_display("Tile centre", centre=c)

    def _toggle_t0(self):
        self._set_display("T = 0 lines",
                          show_t0=self.act_show_t0.isChecked())

    # File
    def new_diagram(self):
        if self._discard_ok():
            self.doc.open_new()

    def open_dialog(self):
        if not self._discard_ok():
            return
        p, _ = QFileDialog.getOpenFileName(
            self, "Open", "", "Phase Tiles (*.phtiles)")
        if p:
            try:
                self.doc.open(p)
            except (OSError, ValueError, KeyError, TypeError,
                    zipfile.BadZipFile) as e:
                # a slot's exception only reaches stderr, so without
                # this a bad file did nothing, silently
                self.statusBar().showMessage(
                    f"Could not open {Path(p).name}: {e}")

    def save(self):
        if self.doc.path is None:
            return self.save_as_dialog()
        self._save(self.doc.path)

    def save_as_dialog(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Save As", "diagram.phtiles",
            "Phase Tiles (*.phtiles)")
        if p:
            self._save(p)

    def _save(self, p):
        # like open_dialog: a slot's exception reaches only stderr, so
        # a read-only folder looked like a save that worked
        old = self.doc.path
        try:
            self.doc.save(p)
        except OSError as e:
            self.doc.path = old
            self.statusBar().showMessage(
                f"Could not save {Path(p).name}: {e}")

    def export_dialog(self):
        from phasetilesapp.export import export_image
        p, _ = QFileDialog.getSaveFileName(
            self, "Export Image", "diagram.png",
            "PNG (*.png);;SVG (*.svg);;JPEG (*.jpg)")
        if p:
            try:
                export_image(self.doc, p)
            except OSError as e:
                self.statusBar().showMessage(
                    f"Could not export {Path(p).name}: {e}")
                return
            self.statusBar().showMessage(f"Exported {p}", 6000)

    def preferences(self):
        from phasetilesapp.preferences import PreferencesDialog
        PreferencesDialog(self.settings, self.doc, self).exec()

    # Run
    def run(self):
        from phasetilesapp.run_controller import RunController
        self.runner = RunController(self.doc, self.settings.workers,
                                    self)
        self.runner.started.connect(self._run_started)
        self.runner.progress.connect(
            lambda d, t: self.progress.setValue(d))
        self.runner.finished.connect(self._run_finished)
        self.runner.failed.connect(self._run_failed)
        self.running = True
        self._refresh()
        self.runner.start()

    def stop(self):
        if self.runner:
            self.runner.stop()

    def _run_started(self, total):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(0)
        self.progress.show()
        self.statusBar().showMessage(f"Running {total} tiles…")

    def _run_finished(self, n, stopped):
        self.running = False
        self.progress.hide()
        if self.runner.error:
            msg = (f"Run failed after {n} tiles ({self.runner.error}); "
                   "the tiles computed are kept.")
            self.statusBar().showMessage(msg)
        else:
            self.statusBar().showMessage(
                f"{n} tiles computed"
                + (" (stopped)" if stopped else ""), 8000)
        self._refresh()

    def _run_failed(self, why):
        print("run failed:", why, file=sys.stderr)

    def about(self):
        from phasetiles import __version__
        QMessageBox.about(self, "Phase Tiles",
                          f"Phase Tiles {__version__}")

    def _discard_ok(self):
        if not self.doc.modified:
            return True
        r = QMessageBox.question(self, "Phase Tiles",
                                 "Discard unsaved changes?")
        return r == QMessageBox.StandardButton.Yes

    def closeEvent(self, ev):
        if self._discard_ok():
            if self.runner is not None and self.runner.is_running():
                self.runner.stop_and_wait()
            ev.accept()
        else:
            ev.ignore()
