from PySide6.QtGui import QImage

from phasetiles import runner
from phasetiles.spec import Axis, MCSettings
from phasetilesapp import export


def _tiny(doc):
    doc.set_spec(doc.spec.replace(
        x=Axis("J1", -1, 1, 1.0), y=Axis("J2", -1, 1, 1.0),
        mc=MCSettings(n=12, anneal=150, equil=150, snaps=2)), "tiny")
    runner.run_tiles(doc.spec, doc.store, 1)


def test_png_export_has_the_requested_size_and_is_not_blank(window,
                                                            tmp_path):
    w = window()
    _tiny(w.doc)
    p = export.export_image(w.doc, tmp_path / "d.png", 1200, 600)
    img = QImage(str(p))
    assert (img.width(), img.height()) == (1200, 600)
    colours = {img.pixel(x, y) for x in range(0, 1200, 37)
               for y in range(0, 600, 29)}
    assert len(colours) > 10


def test_svg_export_writes_vector_text(window, tmp_path):
    w = window()
    _tiny(w.doc)
    p = export.export_image(w.doc, tmp_path / "d.svg")
    assert "<svg" in p.read_text() and "J1" in p.read_text()


def test_export_menu_writes_where_the_dialog_says(window, tmp_path,
                                                  monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    w = window()
    _tiny(w.doc)
    target = tmp_path / "menu.png"
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (str(target),
                                                      "PNG (*.png)")))
    w.act_export.trigger()
    assert target.exists()


def test_preferences_apply_sets_workers_and_rcsr(window, tmp_path):
    from phasetiles import nets
    from phasetilesapp.preferences import PreferencesDialog
    w = window()
    f = tmp_path / "mini.cgd"
    f.write_text("CRYSTAL\n  NAME sql\n  GROUP p4mm\n"
                 "  CELL 1.0 1.0 90.0\n  NODE 1 4 0.0 0.0\n"
                 "  EDGE 0.0 0.0 0.0 1.0\nEND\n")
    d = PreferencesDialog(w.settings, w.doc, w)
    d.workers.setValue(3)
    d.rcsr.setText(str(f))
    d.apply()
    try:
        assert w.settings.workers == 3
        assert list(nets.list_2d()) == ["sql"]
    finally:
        d.rcsr.setText("")
        d.apply()


def test_a_missing_rcsr_file_at_startup_falls_back_and_says_so(
        window, tmp_path):
    from PySide6.QtCore import QSettings

    from phasetiles import nets
    q = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                  "PhaseTiles", "Phase Tiles")
    q.setValue("data/rcsr_path", str(tmp_path / "gone.cgd"))
    q.sync()
    w = window()
    assert "sql" in nets.list_2d() and len(nets.list_2d()) > 1
    assert "gone.cgd" in w.statusBar().currentMessage()
