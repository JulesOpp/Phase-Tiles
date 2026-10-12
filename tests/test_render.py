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
