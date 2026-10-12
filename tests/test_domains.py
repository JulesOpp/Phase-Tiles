import numpy as np

from phasetiles import domains, nets, scattering
from phasetiles.mc import Lattice


def _stripes(n):
    """Left half: stripes along x; right half: along y."""
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    a = np.where(i % 2, 1, -1)
    b = np.where(j % 2, 1, -1)
    return np.where(j < n // 2, a, b).astype(np.int8).ravel()


def test_two_stripe_orientations_are_two_domains_with_a_wall():
    net, n = nets.Net("sql", nshell=1), 24
    s = _stripes(n)
    C = scattering.correlations(Lattice(net, n, 1), s[None])
    dm = domains.domain_map(net, n, s, C, [(12, 0), (0, 12)])
    o = dm.orientation.reshape(n, n)
    assert len(set(o[:, 2:9].ravel()) - {-1}) == 1
    assert len(set(o[:, 15:22].ravel()) - {-1}) == 1
    assert o[0, 4] != o[0, 18]


def test_antiphase_halves_get_different_translations():
    net, n = nets.Net("sql", nshell=1), 24
    i = np.arange(n)[:, None] + np.zeros(n, int)
    s = np.where(i % 2, 1, -1)
    s[n // 2:] *= -1
    s = s.astype(np.int8).ravel()
    C = scattering.correlations(Lattice(net, n, 1), s[None])
    dm = domains.domain_map(net, n, s, C, [(12, 0)])
    t = dm.translation.reshape(n, n)
    assert t[3, 5] != t[18, 5]


def test_ferro_up_and_down_regions_are_distinct():
    net, n = nets.Net("sql", nshell=1), 24
    s = np.ones((n, n), np.int8)
    s[:, n // 2:] = -1
    s = s.ravel()
    C = scattering.correlations(Lattice(net, n, 1), s[None])
    dm = domains.domain_map(net, n, s, C, [(0, 0)])
    t = dm.translation.reshape(n, n)
    assert t[5, 3] != t[5, 18]


def test_honeycomb_neel_is_one_domain_without_walls():
    net, n = nets.Net("hcb", nshell=1), 12
    s = np.tile(np.array([1, -1], np.int8), n * n)
    C = scattering.correlations(Lattice(net, n, 1), s[None])
    dm = domains.domain_map(net, n, s, C, [(0, 0)])
    assert (dm.orientation == 0).all()
    assert len(set(dm.translation.tolist())) == 1


def test_positions_follow_the_mc_site_order():
    net = nets.Net("kgm", nshell=1)
    p = domains.site_positions(net, 4)
    assert p.shape == (4 * 4 * 3, 2)
    assert np.allclose(p[1], net.frac[1] @ net.A)
