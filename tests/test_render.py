import numpy as np

from phasetiles import nets, render


def test_flat_tiles_stay_light_and_peaks_go_black():
    flat = np.ones((8, 8))
    assert render.log_tile(flat, 2.5, 1.0).max() < 0.2
    pk = np.ones((8, 8))
    pk[0, 0] = 1e4
    assert render.log_tile(pk, 2.5, 1.0).max() == 1.0


def test_splat_is_isotropic_on_a_hexagonal_grid():
    net = nets.Net("hxl", nshell=1)
    inten = np.zeros((24, 24))
    inten[0, 0] = 1.0
    r = 0.02
    ang = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    Q = np.c_[r * np.cos(ang), r * np.sin(ang)]
    v = render.splat(inten, net, Q)
    assert v.std() / v.mean() < 0.05


def _splat_reference(grid, net, Qpix, sigma):
    """Normalised Gaussian sum over every grid point, no window."""
    n = grid.shape[0]
    B = np.linalg.inv(net.A).T
    m = np.stack(np.meshgrid(np.arange(-n, 2 * n), np.arange(-n, 2 * n),
                             indexing="ij"), -1).reshape(-1, 2)
    h = min(np.linalg.norm(B, axis=1)) / n
    d = np.linalg.norm(Qpix[:, None, :] - (m / n) @ B, axis=-1)
    w = np.exp(-0.5 * (d / (sigma * h)) ** 2)
    v = grid[m[:, 0] % n, m[:, 1] % n]
    return (w * v).sum(1) / w.sum(1)


def test_splat_matches_a_full_gaussian_sum():
    net = nets.Net("hcb", nshell=1)
    rng = np.random.default_rng(0)
    grid = rng.random((12, 12))
    Q = rng.random((20, 2)) @ np.linalg.inv(net.A).T  # one cell
    got = render.splat(grid, net, Q, sigma=0.8)
    assert np.allclose(got, _splat_reference(grid, net, Q, 0.8),
                       atol=2e-3)


def test_tiles_of_one_diagram_share_their_splat_weights():
    net = nets.Net("sql", nshell=1)
    _, poly = __import__("phasetiles.tiling", fromlist=["x"]).recip(net)
    render._WEIGHTS.clear()
    for k in range(5):
        render.tile_image(np.full((24, 24), 1.0 + k), net, poly)
    assert len(render._WEIGHTS) == 1
