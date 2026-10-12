from phasetiles import runner
from phasetiles.spec import Axis, MCSettings
from phasetiles.tiling import TileCentre
from phasetilesapp.diagram_painter import DiagramModel
from phasetilesapp.domains_panel import DomainsPanel


class StubView:
    """Stands in for the painted view: records what it was given."""
    def __init__(self):
        self.calls = []

    def set_data(self, pos, colours, cell):
        self.calls.append((len(pos), len(colours)))

    def widget(self):
        from PySide6.QtWidgets import QWidget
        return QWidget()


def _panel(window, stub=None):
    w = window(make_domain_view=(lambda: stub) if stub else None)
    return w, w.findChild(DomainsPanel)


def test_no_selection_invites_a_click(window):
    _, p = _panel(window)
    assert "Click a tile" in p.info.text()


def test_an_uncomputed_tile_says_so_without_raising(window):
    w, p = _panel(window)
    w.doc.select(TileCentre(0.0, 0.0, 10, 10))
    assert "not computed yet" in p.info.text()


def test_a_computed_tile_shows_its_sites(window):
    stub = StubView()
    w, p = _panel(window, stub)
    w.doc.set_spec(w.doc.spec.replace(
        x=Axis("J1", -1, -1, 1.0), y=Axis("J2", 0, 0, 1.0),
        mc=MCSettings(n=12, anneal=300, equil=200, snaps=2)), "one")
    runner.run_tiles(w.doc.spec, w.doc.store, 1)
    w.doc.notify_tiles()
    w.doc.select(DiagramModel.build(w.doc).tiles[0].centre)
    assert stub.calls[-1] == (144, 144)
    assert "q = (1/2, 1/2)" in p.info.text()
    p.mode.setCurrentText("Domains")
    assert "q = (1/2, 1/2)" in p.legend.text()


def test_selection_during_a_run_updates_when_the_tile_arrives(window):
    stub = StubView()
    w, p = _panel(window, stub)
    w.doc.set_spec(w.doc.spec.replace(
        x=Axis("J1", 1, 1, 1.0), y=Axis("J2", 0, 0, 1.0),
        mc=MCSettings(n=12, anneal=100, equil=100, snaps=2)), "one")
    t = DiagramModel.build(w.doc).tiles[0].centre
    w.doc.select(t)
    assert "not computed yet" in p.info.text()
    runner.run_tiles(w.doc.spec, w.doc.store, 1)
    w.doc.notify_tiles()
    assert "ferro" in p.info.text()
