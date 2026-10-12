"""Tile pixels as numbers; the GUI turns them into a QImage.

Isotropic Gaussian splatting in Cartesian q, because bilinear
interpolation on an oblique (hexagonal) grid draws every Bragg peak
as a skewed rhombus.  Each tile is on its own log scale, anchored at
half its median so flat (disordered) tiles stay light instead of
filling the range and going black.  No matplotlib: the point-in-
polygon test below is the only geometry needed.
"""
import itertools

import numpy as np

from phasetiles.tiling import CENTRES


def log_tile(img, dyn, med):
    lo = np.log10(0.5 * med)
    top = max(np.log10(np.nanmax(img)), lo + dyn)
    return np.clip((np.log10(np.maximum(img, 1e-30)) - lo)
                   / (top - lo), 0, 1)


def splat(grid, net, Qpix, sigma=None):
    """Sample the periodic grid function grid[m1, m2] (q = m/n) at
    Cartesian points Qpix, Gaussian width sigma grid spacings."""
    n = grid.shape[0]
    B = np.linalg.inv(net.A).T
    hk = Qpix @ net.A.T * n
    base = np.floor(hk).astype(int)
    h = min(np.linalg.norm(B, axis=1)) / n
    sigma = sigma or max(0.55, 0.03 * n)   # >= 3 % of the zone width
    r = int(np.ceil(2.5 * sigma))
    num = np.zeros(hk.shape[:-1])
    den = np.zeros(hk.shape[:-1])
    for d in itertools.product(range(-r, r + 2), repeat=2):
        p = base + np.array(d)
        dq = ((p - hk) / n) @ B
        w = np.exp(-0.5 * (np.linalg.norm(dq, axis=-1)
                           / (sigma * h)) ** 2)
        num += w * grid[p[..., 0] % n, p[..., 1] % n]
        den += w
    return num / den


def _inside(pts, poly):
    """Convex polygon, vertices counter-clockwise (tiling.recip)."""
    ok = np.ones(len(pts), bool)
    for a, b in zip(poly, np.roll(poly, -1, axis=0), strict=True):
        cross = ((b[0] - a[0]) * (pts[:, 1] - a[1])
                 - (b[1] - a[1]) * (pts[:, 0] - a[0]))
        ok &= cross >= -1e-12
    return ok


def tile_image(inten, net, poly, centre="gamma", npx=81, dyn=2.5):
    """(npx, npx) values in 0..1, NaN outside the tile; row 0 is the
    lowest q_y.  The tile shape never moves; `centre` shifts what is
    sampled inside it."""
    B = np.linalg.inv(net.A).T
    q0 = np.array(CENTRES[centre]) @ B
    lo, hi = poly.min(0), poly.max(0)
    gx, gy = np.meshgrid(np.linspace(lo[0], hi[0], npx),
                         np.linspace(lo[1], hi[1], npx))
    Q = np.stack([gx, gy], -1).reshape(-1, 2)
    img = log_tile(splat(inten, net, Q + q0), dyn,
                   float(np.median(inten)) + 1e-9)
    img[~_inside(Q, poly)] = np.nan
    return img.reshape(npx, npx), (lo[0], hi[0], lo[1], hi[1])
