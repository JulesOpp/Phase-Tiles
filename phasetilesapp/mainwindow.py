"""The shell: menus, docks, status.  No physics here -- every action
asks the Document or the core."""
import dataclasses

from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from phasetilesapp.document import Document
from phasetilesapp.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self, document=None, make_domain_view=None):
        super().__init__()
        self.settings = Settings()
        self.doc = document or Document(
            store_root=self.settings.cache_root)
        self._make_domain_view = make_domain_view
        self.setWindowTitle("Phase Tiles")
        self.resize(1400, 860)
        self._build_actions()
        self._build_menus()
        from phasetilesapp.diagram_view import DiagramView
        self.diagram = DiagramView(self.doc)
        self.setCentralWidget(self.diagram)
        self.doc.specChanged.connect(self._refresh)
        self.doc.modifiedChanged.connect(self._refresh)
        self._refresh()

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
            self.doc.open(p)

    def save(self):
        if self.doc.path is None:
            return self.save_as_dialog()
        self.doc.save()

    def save_as_dialog(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Save As", "diagram.phtiles",
            "Phase Tiles (*.phtiles)")
        if p:
            self.doc.save(p)

    def export_dialog(self):          # Task 13
        pass

    def preferences(self):            # Task 13
        pass

    def run(self):                    # Task 11
        pass

    def stop(self):                   # Task 11
        pass

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
            ev.accept()
        else:
            ev.ignore()
