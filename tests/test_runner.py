import pytest

from phasetiles import runner
from phasetiles.spec import Axis, MCSettings, default_spec
from phasetiles.store import ResultStore


def _tiny():
    return default_spec().replace(
        x=Axis("J1", -1, 1, 2.0), y=Axis("J2", 0, 0, 1.0),
        mc=MCSettings(n=12, anneal=100, equil=100, snaps=2))


def test_runs_only_missing_tiles(tmp_path):
    st, s = ResultStore(tmp_path), _tiny()
    got = []
    assert runner.run_tiles(s, st, 1, on_tile=got.append) == 2
    assert len(got) == 2
    assert runner.jobs_for(s, st) == []
    assert runner.run_tiles(s, st, 1) == 0


def test_stop_leaves_no_partial_results(tmp_path):
    st, s = ResultStore(tmp_path), _tiny()
    assert runner.run_tiles(s, st, 1, should_stop=lambda: True) == 0
    assert len(runner.jobs_for(s, st)) == 2


@pytest.mark.slow
def test_process_pool_gives_the_same_tiles(tmp_path):
    a, b, s = ResultStore(tmp_path / "a"), ResultStore(tmp_path / "b"), \
        _tiny()
    assert runner.run_tiles(s, a, 2) == 2
    runner.run_tiles(s, b, 1)
    p = s.params_at(-1.0, 0.0)
    assert (a.get(s, p).snap == b.get(s, p).snap).all()
