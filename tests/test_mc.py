import numpy as np
import pytest

from phasetiles import mc, nets, scattering


@pytest.fixture(scope="module")
def sql():
    return mc.Lattice(nets.Net("sql", nshell=2), 24, 2)


@pytest.mark.parametrize("J,q", [((-1, 0), (12, 12)),
                                 ((-0.3, -1), (0, 12)),
                                 ((1, 0), (0, 0))])
def test_square_mc_finds_neel_stripe_and_ferro(sql, J, q):
    r = mc.run_mc(sql, J, 0.0, 0.3, 1000, 500, 5, 1)
    C = scattering.correlations(sql, r.snaps)[..., 0, 0].real
    assert tuple(sorted(np.unravel_index(C.argmax(), C.shape))) == q


def test_no_two_sites_of_a_colour_interact(sql):
    A = sum(sql.adj).tocsr()
    for c in sql.colours:
        assert A[c][:, c].nnz == 0


def test_perfect_order_gives_order_parameter_one(sql):
    s = np.where((np.arange(24)[:, None] + np.arange(24)) % 2, 1, -1)
    C = scattering.correlations(sql, s.reshape(1, -1).astype(np.int8),
                                subtract_mean=True)
    assert np.isclose(scattering.order_params(C)[12, 12], 1.0)


def test_folded_intensity_equals_s_of_q_for_one_site_per_cell(sql):
    r = mc.run_mc(sql, (-1, 0), 0.0, 1.0, 50, 50, 2, 3)
    C = scattering.correlations(sql, r.snaps)
    assert np.allclose(scattering.folded_intensity(C, sql.net),
                       C[..., 0, 0].real)


def test_honeycomb_neel_is_staggered_q0():
    lat = mc.Lattice(nets.Net("hcb", nshell=1), 12, 1)
    r = mc.run_mc(lat, (-1,), 0.0, 0.3, 800, 300, 3, 1)
    C = scattering.correlations(lat, r.snaps, subtract_mean=True)
    phi2 = scattering.order_params(C)
    assert phi2[0, 0] > 0.8


def test_a_stop_request_cancels_the_run(sql):
    with pytest.raises(mc.Cancelled):
        mc.run_mc(sql, (-1, 0), 0.0, 0.5, 1000, 1000, 5, 1,
                  should_stop=lambda: True)
