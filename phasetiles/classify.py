"""Name the phase of one tile from its order parameters.

The dominant ordering wavevector is taken per *star* (all q related
by the point group, and q ~ -q), so a stripe state split into two
orientation domains is still one phase.  Peaks within 1.5 grid steps
of a commensurate q (denominator <= 6) are merged onto it: they are
domain-broadened, not incommensurate.
"""
import itertools
from dataclasses import dataclass
from fractions import Fraction

import numpy as np


@dataclass
class Phase:
    label: str
    amplitude: float
    star: list           # grid indices (m1, m2), one per +-q pair


class QLab(dict):
    """grid q -> star key (after merging), with .exact the unmerged
    map that defines which q belong to a star."""

    def __init__(self, merged, exact):
        super().__init__(merged)
        self.exact = exact


def canonical_q(net, n):
    """Map each grid q = (m1, m2)/n to a canonical member of its star
    under the point group (+ q -> -q)."""
    Rs = {tuple(R.ravel().astype(int)): R for R, _ in net.ops}
    RT = [np.linalg.inv(R).T for R in Rs.values()]
    lab = {}
    for m1, m2 in itertools.product(range(n), repeat=2):
        q = np.array([m1, m2])
        star = []
        for M in RT:
            for sg in (1, -1):
                v = np.round(sg * M @ q).astype(int) % n
                star.append((int(v[0]), int(v[1])))
        lab[(m1, m2)] = min(star)
    exact = dict(lab)
    comm = {(int(round(n * a / d)) % n, int(round(n * b / d)) % n)
            for d in range(1, 7) for a in range(d) for b in range(d)
            if n * a % d == 0 and n * b % d == 0}
    comm = sorted({lab[c] for c in comm})

    def dist(k, c):
        return max(abs((k[0] - c[0] + n // 2) % n - n // 2),
                   abs((k[1] - c[1] + n // 2) % n - n // 2))
    if n >= 24:
        for q, k in lab.items():
            d = [dist(k, c) for c in comm]
            if 0 < min(d) <= 1.5:
                lab[q] = comm[int(np.argmin(d))]
    return QLab(lab, exact)


def frac_label(m, n):
    def s(x):
        if x == 0:
            return "0"
        if x.denominator == 1:
            return f"{x.numerator}"
        return f"{x.numerator}/{x.denominator}"
    f = [Fraction(int(x), n).limit_denominator(n) for x in m]
    return f"q = ({s(f[0])}, {s(f[1])})"


def _star(qlab, key, n):
    """The exact symmetry images of `key` (not merged neighbours), one
    of each +-q pair: the q's a domain map looks for."""
    seen, out = set(), []
    for q in sorted(q for q, k in qlab.exact.items() if k == key):
        if q not in seen:
            out.append(q)
            seen |= {q, ((-q[0]) % n, (-q[1]) % n)}
    return out


def classify(phi2, absm, n, qlab, phi0, nsub):
    acc = {}
    for (m1, m2), k in qlab.items():
        acc[k] = acc.get(k, 0.0) + phi2[m1, m2]
    keys = sorted(acc, key=acc.get, reverse=True)
    pq = float(np.sqrt(acc[keys[0]]))
    pm = float(absm)
    if max(pm, pq) < phi0:
        return Phase("disordered", max(pm, pq), [])
    # (0, 0) on one site per cell = ferro split into up/down domains
    if pm >= pq or (keys[0] == (0, 0) and nsub == 1):
        return Phase("ferro (q = 0)", max(pm, pq), [(0, 0)])
    lab = frac_label(keys[0], n)
    if keys[0] == (0, 0):
        lab += " staggered"
    star = _star(qlab, keys[0], n)
    if len(keys) > 1 and np.sqrt(acc[keys[1]]) > max(0.5 * pq, phi0):
        lab = (f"multi-q ({frac_label(keys[0], n)[4:]} + "
               f"{frac_label(keys[1], n)[4:]})")
        star += _star(qlab, keys[1], n)
    return Phase(lab, pq, star)
