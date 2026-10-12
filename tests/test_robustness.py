"""Final-review findings: a spec Run refuses must still paint, a run
that dies must not leave the window "Running", and a project or net
source the app cannot use must be refused with a sentence."""
import zipfile

import pytest
from PySide6.QtWidgets import QFileDialog

from phasetiles.spec import Axis
from phasetilesapp.diagram_painter import DiagramModel


@pytest.mark.parametrize("x", [
    Axis("J1", -1, 1, 0.0),          # step 0: ZeroDivisionError
    Axis("J1", 1, -1, 0.5),          # reversed: IndexError in T = 0
    Axis("J1", -1, 1, 0.01),         # 201 x 201: over the tile cap
])
def test_a_spec_run_refuses_paints_its_reason_not_tiles(window, x):
    w = window()
    y = Axis("J2", -1, 1, 0.01) if x.step == 0.01 else w.doc.spec.y
    w.doc.set_spec(w.doc.spec.replace(x=x, y=y), "bad")
    m = DiagramModel.build(w.doc)
    assert m.tiles == [] and m.error
    assert w.diagram.grab().width() > 0       # paints without raising


def test_the_step_boxes_cannot_be_set_to_zero(window):
    from phasetilesapp.setup_dock import SetupDock
    d = window().findChild(SetupDock)
    assert d.x_step.minimum() > 0 and d.y_step.minimum() > 0


def test_a_run_that_dies_says_so_and_stops_running(window, qtbot,
                                                   monkeypatch):
    from phasetiles import runner

    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(runner, "run_tiles", boom)
    w = window()
    w.doc.set_spec(w.doc.spec.replace(x=Axis("J1", -1, 1, 2.0),
                                      y=Axis("J2", 0, 0, 1.0)), "two")
    w.act_run.trigger()
    qtbot.waitUntil(lambda: not w.running, timeout=10000)
    assert w.act_run.isEnabled() and not w.act_stop.isEnabled()
    assert "disk full" in w.statusBar().currentMessage()


def _open(w, monkeypatch, path):
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (str(path), "")))
    w.open_dialog()


def test_a_corrupt_project_is_refused_with_a_sentence(window, tmp_path,
                                                      monkeypatch):
    w = window()
    before = w.doc.spec
    bad = tmp_path / "bad.phtiles"
    bad.write_bytes(b"not a zip")
    _open(w, monkeypatch, bad)
    assert w.doc.spec == before
    assert "bad.phtiles" in w.statusBar().currentMessage()


def test_a_project_on_an_unknown_net_is_refused(window, tmp_path,
                                                monkeypatch):
    w = window()
    before = w.doc.spec
    p = tmp_path / "zzz.phtiles"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("spec.json", before.replace(net="zzz").to_json())
    _open(w, monkeypatch, p)
    assert w.doc.spec == before and w.doc.path is None
    assert "zzz" in w.statusBar().currentMessage()
    assert w.doc.net.name == "sql"              # still usable


def test_preferences_refuse_a_net_file_without_the_current_net(
        window, tmp_path):
    from phasetilesapp.preferences import PreferencesDialog
    w = window()
    f = tmp_path / "other.cgd"
    f.write_text("CRYSTAL\n  NAME zzz\n  GROUP p1\n  CELL 1 1 90\n"
                 "  NODE 1 4 0 0\nEND\n", encoding="utf-8")
    dlg = PreferencesDialog(w.settings, w.doc, w)
    dlg.rcsr.setText(str(f))
    assert dlg.apply() is False
    assert "sql" in dlg.error.text()
    assert w.doc.net.name == "sql"              # still usable


def _computed(w):
    from phasetiles import runner
    from phasetiles.spec import Axis, MCSettings
    w.doc.set_spec(w.doc.spec.replace(
        x=Axis("J1", -1, 1, 2.0), y=Axis("J2", 0, 0, 1.0),
        mc=MCSettings(n=12, anneal=50, equil=50, snaps=1)), "tiny")
    runner.run_tiles(w.doc.spec, w.doc.store, 1)
    w.doc.notify_tiles()


def test_clear_cache_removes_the_tiles_and_the_diagram_forgets_them(
        window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from phasetilesapp.diagram_painter import DiagramModel
    from phasetilesapp.preferences import PreferencesDialog
    w = window()
    _computed(w)
    assert any(t.image is not None
               for t in DiagramModel.build(w.doc).tiles)
    dlg = PreferencesDialog(w.settings, w.doc, w)
    assert "2 tiles" in dlg.cache_info.text()
    monkeypatch.setattr(QMessageBox, "question", staticmethod(
        lambda *a, **k: QMessageBox.StandardButton.Yes))
    dlg.clear_cache.click()
    assert w.doc.store.usage() == (0, 0)
    assert "0 tiles" in dlg.cache_info.text()
    assert all(t.image is None
               for t in DiagramModel.build(w.doc).tiles)


def test_clear_cache_keeps_the_tiles_when_the_user_says_no(
        window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from phasetilesapp.preferences import PreferencesDialog
    w = window()
    _computed(w)
    dlg = PreferencesDialog(w.settings, w.doc, w)
    monkeypatch.setattr(QMessageBox, "question", staticmethod(
        lambda *a, **k: QMessageBox.StandardButton.No))
    dlg.clear_cache.click()
    assert w.doc.store.usage()[0] == 2


def test_clear_cache_is_disabled_during_a_run(window):
    from phasetilesapp.preferences import PreferencesDialog
    w = window()
    w.running = True
    dlg = PreferencesDialog(w.settings, w.doc, w)
    assert not dlg.clear_cache.isEnabled()
