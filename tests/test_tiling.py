import numpy as np

from phasetiles import nets, render, tiling
from phasetiles.spec import Axis

X, Y = Axis("J1", -1, 1, 0.5), Axis("J2", -1, 1, 0.5)


def _area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def test_square_tiles_form_the_parameter_grid():
    B, poly = tiling.recip(nets.Net("sql", nshell=1))
    c = tiling.tile_centres(B, X, Y)
    assert len(c) == 25
    assert sorted({t.x for t in c}) == [-1, -.5, 0, .5, 1]
    assert sorted({t.y for t in c}) == [-1, -.5, 0, .5, 1]
    assert len(poly) == 4


def test_hexagonal_tiles_are_hexagons_with_alternate_columns_shifted():
    B, poly = tiling.recip(nets.Net("hxl", nshell=1))
    assert len(poly) == 6
    c = tiling.tile_centres(B, X, Y)
    odd = sorted({t.y for t in c if t.c % 2})
    assert np.isclose(odd[0] % 0.5, 0.25)


def test_tile_polygons_tile_the_plane_without_overlap():
    for name in ("sql", "hxl", "kgm"):
        B, poly = tiling.recip(nets.Net(name, nshell=1))
        mx, my = tiling.scale(B, X, Y)
        a = _area(tiling.tile_polygon(poly, mx, my, 0, 0))
        assert np.isclose(a, X.step * Y.step), name


def test_half_centre_shifts_content_not_tile_shape():
    net = nets.Net("hxl", nshell=1)
    _, poly = tiling.recip(net)
    inten = np.zeros((12, 12))
    inten[0, 0] = 100.0                     # a Gamma peak
    g, _ = render.tile_image(inten, net, poly, "gamma", npx=41)
    h, _ = render.tile_image(inten, net, poly, "half", npx=41)
    assert np.isnan(g).sum() == np.isnan(h).sum()  # same tile shape
    assert np.nanargmax(g) == 20 * 41 + 20         # peak at centre
    assert np.nanargmax(h) != 20 * 41 + 20         # moved off centre
