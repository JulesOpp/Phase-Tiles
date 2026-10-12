import numpy as np

from phasetiles.spec import default_spec
from phasetiles.store import TileResult
from phasetilesapp.document import Document


def _put(doc, x, y):
    p = doc.spec.params_at(x, y)
    doc.store.put(doc.spec, p, TileResult(
        p, np.zeros((2, 2, 1, 1), np.complex64), np.zeros((2, 2)),
        np.ones(4, np.int8), 0.0, 1.0, -2.0))


def test_set_spec_is_one_undo_step_and_emits(qtbot, tmp_path):
    d = Document(store_root=tmp_path)
    with qtbot.waitSignal(d.specChanged):
        d.set_spec(d.spec.replace(net="kgm"), "Change net")
    assert d.modified
    d.undo()
    assert d.spec.net == "sql" and not d.modified


def test_undo_of_a_net_change_shows_the_old_tiles_again(qtbot,
                                                        tmp_path):
    from phasetiles.tiling import TileCentre
    d = Document(store_root=tmp_path)
    _put(d, 0.0, 0.0)
    t = TileCentre(0.0, 0.0, 2, 2)
    assert d.tile_result(t) is not None
    d.set_spec(d.spec.replace(net="kgm"), "Change net")
    assert d.tile_result(t) is None
    d.undo()
    assert d.tile_result(t) is not None


def test_save_and_open_round_trip(qtbot, tmp_path):
    d = Document(store_root=tmp_path / "a")
    _put(d, 0.0, 0.0)
    d.save(tmp_path / "x.phtiles")
    assert not d.modified
    e = Document(store_root=tmp_path / "b")
    e.open(tmp_path / "x.phtiles")
    assert e.spec == d.spec and e.path.name == "x.phtiles"


def test_new_resets_to_the_default_diagram(qtbot, tmp_path):
    d = Document(store_root=tmp_path)
    d.set_spec(d.spec.replace(net="kgm"), "x")
    d.open_new()
    assert d.spec == default_spec() and not d.modified


def test_a_net_change_clears_the_selection(qtbot, tmp_path):
    from phasetiles.tiling import TileCentre
    d = Document(store_root=tmp_path)
    d.select(TileCentre(0.0, 0.0, 0, 0))
    d.set_spec(d.spec.replace(net="kgm"), "Change net")
    assert d.selected is None
