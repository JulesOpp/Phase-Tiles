import numpy as np

from phasetiles import groundstate, nets
from phasetiles.spec import Axis, default_spec


def _b(bs, xs, ys, lab, x, y):
    i, j = np.argmin(abs(xs - x)), np.argmin(abs(ys - y))
    return tuple(bs[lab[i, j], :2])


def test_square_j1_j2_boundaries_are_at_half_j1():
    s = default_spec()
    bs = groundstate.sums(nets.Net("sql", nshell=2), 2)
    xs, ys, lab = groundstate.label_grid(bs, s, npts=201)
    assert _b(bs, xs, ys, lab, -1, 0.2) == (-2, 2)      # Neel
    assert _b(bs, xs, ys, lab, -1, -0.6) == (0, -2)     # stripe
    assert _b(bs, xs, ys, lab, -1, -0.4) == (-2, 2)
    assert _b(bs, xs, ys, lab, 1, -0.4) == (2, 2)       # ferro
    assert _b(bs, xs, ys, lab, 1, -0.6) == (0, -2)


def test_boundary_segments_lie_on_the_exact_lines():
    s = default_spec()
    bs = groundstate.sums(nets.Net("sql", nshell=2), 2)
    seg = groundstate.segments(*groundstate.label_grid(bs, s, 201))
    mid = seg.mean(axis=1)
    on = (np.isclose(mid[:, 1], mid[:, 0] / 2, atol=0.02)
          | np.isclose(mid[:, 1], -mid[:, 0] / 2, atol=0.02)
          | np.isclose(mid[:, 0], 0, atol=0.02))
    assert len(seg) and on.all()


def test_a_net_too_big_to_enumerate_returns_none():
    big = max(nets.list_2d(), key=lambda k: nets.Net(k, 1).nsub)
    assert groundstate.sums(nets.Net(big, nshell=1), 1) is None
    assert "more than 16 sites" in groundstate.unavailable_reason(
        default_spec().replace(net=big), nets.Net(big, nshell=1))


def test_t_on_an_axis_has_no_t0_lines():
    s = default_spec().replace(x=Axis("T", 0.1, 1, 0.1))
    assert "T is an axis" in groundstate.unavailable_reason(
        s, nets.Net("sql", nshell=2))


def test_hull_pruning_matches_brute_force_with_a_field():
    from phasetiles.hamiltonian import Hamiltonian, Term
    s = default_spec().replace(
        net="kgm", hamiltonian=Hamiltonian(terms=(
            Term("pair", 1), Term("pair", 2), Term("field"))),
        fixed=(("H", 0.7), ("T", 0.5)))
    bs = groundstate.sums(nets.Net("kgm", nshell=2), 2)
    xs, ys, lab = groundstate.label_grid(bs, s, npts=61)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    E = -(np.multiply.outer(X, bs[:, 0]) + np.multiply.outer(Y, bs[:, 1])
          + 0.7 * bs[:, 2])
    best = E.min(-1)
    got = np.take_along_axis(E, lab[..., None], -1)[..., 0]
    assert np.allclose(got, best)
