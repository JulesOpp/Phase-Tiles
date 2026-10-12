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
