import numpy as np

from phasetiles.spec import Display, default_spec
from phasetiles.store import ResultStore, TileResult


def _r(p):
    return TileResult(p, np.zeros((2, 2, 1, 1), np.complex64),
                      np.zeros((2, 2)), np.ones(4, np.int8), 0.0, 1.0,
                      -2.0)


def test_round_trip(tmp_path):
    st, s = ResultStore(tmp_path), default_spec()
    p = s.params_at(0, 0)
    st.put(s, p, _r(p))
    assert st.get(s, p).absm == 1.0


def test_a_different_net_never_reads_another_nets_tiles(tmp_path):
    st, s = ResultStore(tmp_path), default_spec()
    p = s.params_at(0, 0)
    st.put(s, p, _r(p))
    assert st.get(s.replace(net="kgm"), p) is None


def test_display_changes_still_find_the_tile(tmp_path):
    st, s = ResultStore(tmp_path), default_spec()
    p = s.params_at(0, 0)
    st.put(s, p, _r(p))
    assert st.has(s.replace(display=Display(centre="half")), p)


def test_a_truncated_file_reads_as_missing_not_a_crash(tmp_path):
    st, s = ResultStore(tmp_path), default_spec()
    p = s.params_at(0, 0)
    st.put(s, p, _r(p))
    f = st.files_for(s)[0]
    f.write_bytes(f.read_bytes()[:20])
    assert st.get(s, p) is None


def test_default_root_follows_the_app_data_variable(app_data):
    from phasetiles.store import default_root
    assert str(default_root()).startswith(app_data)


def test_minus_zero_and_zero_are_the_same_tile(tmp_path):
    # tile_centres can yield -0.0 for a row at 0; a lookup with 0.0
    # (or a value rounding to 0 from below) must find the same file.
    s = ResultStore(tmp_path)
    spec = default_spec()
    k = s.key(spec, {"J1": 1.0, "J2": 0.0, "T": 0.5})
    assert s.key(spec, {"J1": 1.0, "J2": -0.0, "T": 0.5}) == k
    assert s.key(spec, {"J1": 1.0, "J2": -1e-9, "T": 0.5}) == k


def test_clearing_removes_every_tile_and_reports_the_count(tmp_path):
    st, s = ResultStore(tmp_path / "cache"), default_spec()
    for x in (0, 1):
        p = s.params_at(x, 0)
        st.put(s, p, _r(p))
    n, size = st.usage()
    assert n == 2 and size > 0
    assert st.clear() == 2
    assert st.usage() == (0, 0)
    assert st.get(s, s.params_at(0, 0)) is None


def test_clearing_leaves_files_that_are_not_tiles(tmp_path):
    # the cache folder is a preference: it may be shared with other
    # files, and clearing must only take what the store wrote
    st, s = ResultStore(tmp_path), default_spec()
    p = s.params_at(0, 0)
    st.put(s, p, _r(p))
    other = tmp_path / "notes.txt"
    other.write_text("keep me")
    st.clear()
    assert other.read_text() == "keep me"


def test_clearing_a_missing_cache_is_harmless(tmp_path):
    st = ResultStore(tmp_path / "never-made")
    assert st.usage() == (0, 0)
    assert st.clear() == 0
