"""Where tiles go and what shape they are.

A tile is the Wigner-Seitz cell of the net's reciprocal lattice, and
tile centres sit on that lattice (c b1 + r b2), so the tiles fill the
diagram with no gaps whatever the net.  b2 is along y because a1 is
along x, which makes the parameter map diagonal:
x = x0 + c dx, y = y0 + (r + c b1y/b2y) dy -- square nets give the
plain grid, hexagonal nets shift alternate columns by dy/2.
"""
from typing import NamedTuple

import numpy as np
from scipy.spatial import Voronoi

CENTRES = {"gamma": (0.0, 0.0), "half": (0.5, 0.5)}


class TileCentre(NamedTuple):
    x: float
    y: float
    c: int
    r: int


def recip(net):
    """Reciprocal basis (rows b1, b2; cycles per length) and the
    Wigner-Seitz cell around Gamma, counter-clockwise."""
    B = np.linalg.inv(net.A).T
    pts = np.array([i * B[0] + j * B[1]
                    for i in range(-3, 4) for j in range(-3, 4)])
    vor = Voronoi(pts)
    o = int(np.argmin(np.linalg.norm(pts, axis=1)))
    poly = vor.vertices[vor.regions[vor.point_region[o]]]
    return B, poly[np.argsort(np.arctan2(poly[:, 1], poly[:, 0]))]


def scale(B, x, y):
    """Parameter units per reciprocal length unit, along x and y."""
    return x.step / B[0, 0], y.step / B[1, 1]


def tile_centres(B, x, y):
    sh = B[0, 1] / B[1, 1]
    ny = y.count() - 1
    out = []
    for c in range(x.count()):
        f = (c * sh + 0.5) % 1.0 - 0.5     # this column's row shift
        for r in range(-1, ny + 2):
            yy = y.start + (r + f) * y.step
            if (y.start - 0.5 * y.step - 1e-9 <= yy
                    <= y.start + (ny + 0.5) * y.step + 1e-9):
                out.append(TileCentre(round(x.start + c * x.step, 6),
                                      round(yy, 6), c, r))
    return out


def tile_polygon(poly, mx, my, x, y):
    return np.c_[x + poly[:, 0] * mx, y + poly[:, 1] * my]


def bounds(x, y):
    return (x.start - 0.5 * x.step,
            x.start + (x.count() - 0.5) * x.step,
            y.start - 0.5 * y.step,
            y.start + (y.count() - 0.5) * y.step)
