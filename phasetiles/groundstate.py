"""Exact T = 0 phase boundaries, by enumeration.

Every periodic configuration of every n1 x n2 supercell with at most
16 sites is reduced to its per-site bond sums (b_1..b_k, m); the
ground state at a parameter point is the one minimising
E = -sum_k J_k b_k - H m.  Nets with more sites per cell than that
have no supercell to enumerate and get a sentence, not a crash.
"""
import itertools

import numpy as np
from scipy.spatial import ConvexHull, QhullError

MAX_SITES = 16


def sums(net, nshell, max_sites=MAX_SITES):
    if net.nsub > max_sites:
        return None
    rows = []
    ns = net.nsub
    for n1, n2 in itertools.product(range(1, max_sites + 1), repeat=2):
        N = ns * n1 * n2
        if N > max_sites:
            continue
        bits = (np.arange(2 ** N)[:, None] >> np.arange(N)[None, :]) & 1
        cfg = 2 * bits.astype(np.int8) - 1
        b = np.zeros((cfg.shape[0], nshell + 1))

        def idx(a, c, i, n1=n1, n2=n2):
            return ((a % n1) * n2 + (c % n2)) * ns + i
        for k, sh in enumerate(net.shells[:nshell]):
            for c1, c2 in itertools.product(range(n1), range(n2)):
                for i, j, (d1, d2) in sh:
                    b[:, k] += (cfg[:, idx(c1, c2, i)]
                                * cfg[:, idx(c1 + d1, c2 + d2, j)])
            b[:, k] /= N
        b[:, -1] = cfg.mean(1)
        rows.append(np.unique(np.round(b, 6), axis=0))
    if not rows:
        return None
    # np.unique, not a set of tuples: 65536 rows per supercell made
    # the tuple version 2 s per diagram build.
    return np.unique(np.concatenate(rows), axis=0)


def _coefficients(bs, spec):
    """Per state, E = c0 + u X + v Y over the two axes."""
    u, v, c0 = (np.zeros(len(bs)) for _ in range(3))
    cols = [(f"J{k + 1}", -bs[:, k]) for k in range(bs.shape[1] - 1)]
    cols.append(("H", -bs[:, -1]))
    fixed = spec.fixed_dict()
    for sym, col in cols:
        if sym == spec.x.symbol:
            u += col
        elif sym == spec.y.symbol:
            v += col
        else:
            c0 += fixed.get(sym, 0.0) * col
    return np.c_[u, v, c0]


def _candidates(coef):
    """Indices of states that can be a ground state somewhere: a
    linear function is minimised on a hull vertex, so everything
    inside the hull of the coefficient points is skipped.  1159 states
    -> a handful for the square J1-J2 model, 5 s -> 0.05 s."""
    _, first = np.unique(np.round(coef, 9), axis=0, return_index=True)
    pts = coef[first]
    dim = 2 if np.ptp(pts[:, 2]) < 1e-12 else 3
    try:
        hull = ConvexHull(pts[:, :dim], qhull_options="QJ")
        return first[np.unique(hull.vertices)]
    except (QhullError, ValueError):     # too few or degenerate points
        return first


def label_grid(bs, spec, npts=401):
    """Index into bs of the ground state at each point of a grid over
    the axes' ranges."""
    xs = np.linspace(spec.x.start, spec.x.values()[-1], npts)
    ys = np.linspace(spec.y.start, spec.y.values()[-1], npts)
    coef = _coefficients(bs, spec)
    cand = _candidates(coef)
    c = coef[cand]
    E = (c[:, 2][None, None, :] + xs[:, None, None] * c[:, 0]
         + ys[None, :, None] * c[:, 1])
    return xs, ys, cand[E.argmin(-1)]


def segments(xs, ys, labels):
    """Grid-cell edges between differently labelled points.  At 401
    points the steps are 0.25 % of the axis -- invisible -- and
    painting them needs no contouring library."""
    dx, dy = xs[1] - xs[0], ys[1] - ys[0]
    out = []
    i, j = np.nonzero(labels[1:, :] != labels[:-1, :])
    out += [((xs[a] + dx / 2, ys[b] - dy / 2),
             (xs[a] + dx / 2, ys[b] + dy / 2))
            for a, b in zip(i, j, strict=True)]
    i, j = np.nonzero(labels[:, 1:] != labels[:, :-1])
    out += [((xs[a] - dx / 2, ys[b] + dy / 2),
             (xs[a] + dx / 2, ys[b] + dy / 2))
            for a, b in zip(i, j, strict=True)]
    return np.array(out, float).reshape(-1, 2, 2)


def unavailable_reason(spec, net):
    if "T" in (spec.x.symbol, spec.y.symbol):
        return "T = 0 lines unavailable: T is an axis."
    if net.nsub > MAX_SITES:
        return (f"T = 0 lines unavailable: {net.name} has {net.nsub} "
                f"sites per cell, more than {MAX_SITES} sites to "
                "enumerate.")
    return None
