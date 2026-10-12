import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QImage, QPainter

from phasetiles import runner
from phasetiles.spec import Axis, MCSettings
from phasetilesapp.diagram_painter import DiagramModel, DiagramPainter


def _tiny(doc):
    doc.set_spec(doc.spec.replace(
        x=Axis("J1", -1, 1, 1.0), y=Axis("J2", -1, 1, 1.0),
        mc=MCSettings(n=12, anneal=200, equil=200, snaps=2)), "tiny")
    runner.run_tiles(doc.spec, doc.store, 1)
    doc.notify_tiles()


def test_every_tile_gets_an_image_and_a_phase(window):
    w = window()
    _tiny(w.doc)
    m = DiagramModel.build(w.doc)
    assert len(m.tiles) == 9
    assert all(t.image is not None for t in m.tiles)
    assert {t.phase.label for t in m.tiles} >= {"ferro (q = 0)"}


def test_clicking_a_tile_selects_it(window, qtbot):
    w = window()
    _tiny(w.doc)
    v = w.diagram
    v.resize(1200, 600)
    m = v.model()
    t = m.tiles[4]
    pos = v.painter.to_widget(v.rect().toRectF(), m, 0, t.centre.x,
                              t.centre.y)
    qtbot.mouseClick(v, Qt.MouseButton.LeftButton, pos=pos.toPoint())
    assert w.doc.selected == t.centre


def test_clicking_outside_every_tile_clears_the_selection(window,
                                                          qtbot):
    w = window()
    _tiny(w.doc)
    w.doc.select(DiagramModel.build(w.doc).tiles[0].centre)
    qtbot.mouseClick(w.diagram, Qt.MouseButton.LeftButton,
                     pos=QPointF(2, 2).toPoint())
    assert w.doc.selected is None


def test_uncomputed_tiles_paint_as_placeholders(window):
    w = window()
    w.doc.set_spec(w.doc.spec.replace(
        x=Axis("J1", -1, 1, 1.0), y=Axis("J2", -1, 1, 1.0)), "grid")
    m = DiagramModel.build(w.doc)
    assert all(t.image is None and t.phase is None for t in m.tiles)
    img = QImage(800, 400, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    DiagramPainter().paint(p, QRectF(0, 0, 800, 400), m, w.palette())
    p.end()


def test_half_centre_changes_pixels_not_tiles(window):
    w = window()
    _tiny(w.doc)
    a = DiagramModel.build(w.doc)
    w.act_centre_half.trigger()
    b = DiagramModel.build(w.doc)
    assert [t.centre for t in a.tiles] == [t.centre for t in b.tiles]
    ia = a.tiles[0].array
    ib = b.tiles[0].array
    assert not np.allclose(np.nan_to_num(ia), np.nan_to_num(ib))


def test_t0_note_explains_missing_lines(window):
    w = window()
    w.doc.set_spec(w.doc.spec.replace(x=Axis("T", 0.1, 1, 0.3)),
                   "T axis")
    assert "T is an axis" in DiagramModel.build(w.doc).t0_note
