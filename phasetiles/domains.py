"""Real-space domains of one MC snapshot.

For each q of the tile's dominant star, a local complex amplitude
psi_q(r): the spins weighted by the principal eigenvector u of C(q)
(the sublattice pattern -- what makes honeycomb Neel or kagome q = 0
work, not just Bravais nets), times e^{2 pi i q.r}, smoothed with a
Gaussian of `radius` cells.  Orientation domain = argmax_q |psi_q|;
translational (antiphase) domain = arg psi quantised by the order of
q (two for q = 1/2, three for 1/3); below `wall` it is a wall.
"""
from dataclasses import dataclass
from math import gcd

import numpy as np
from scipy import ndimage

from phasetiles.classify import frac_label


@dataclass
class DomainMap:
    orientation: np.ndarray      # per site; -1 = wall / disordered
    translation: np.ndarray
    amplitude: np.ndarray
    names: list
    wall: float


def site_positions(net, n):
    """Cartesian positions in the MC's site order."""
    c1, c2 = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    cells = np.stack([c1.ravel(), c2.ravel()], -1)
    frac = cells[:, None, :] + net.frac[None, :, :]
    return frac.reshape(-1, 2) @ net.A


def _order(m, n):
    d = n // gcd(n, gcd(int(m[0]), int(m[1])))
    return 2 if d == 1 else d          # q = 0: up / down


def _smooth(f, radius):
    return (ndimage.gaussian_filter(f.real, radius, mode="wrap")
            + 1j * ndimage.gaussian_filter(f.imag, radius, mode="wrap"))


def domain_map(net, n, snap, C, star, radius=3.0, wall=0.35):
    ns = net.nsub
    s = snap.reshape(n, n, ns).astype(float)
    c = np.arange(n)
    amps, trans = [], []
    for m in star:
        _, vec = np.linalg.eigh(C[m[0], m[1]])
        u = vec[:, -1]
        u = u / (np.abs(u).sum() or 1.0)
        ph = np.exp(2j * np.pi * np.add.outer(m[0] * c, m[1] * c) / n)
        psi = np.zeros((n, n), complex)
        for i in range(ns):
            ri = np.exp(2j * np.pi * np.dot(np.array(m) / n,
                                            net.frac[i]))
            psi += _smooth(s[..., i] * ph * ri * np.conj(u[i]), radius)
        d = _order(m, n)
        if tuple(m) == (0, 0):
            t = (psi.real < 0).astype(int)
        else:
            t = np.round(np.angle(psi) * d / (2 * np.pi)).astype(int) % d
        amps.append(np.abs(psi))
        trans.append(t)
    A = np.array(amps)
    o = A.argmax(0)
    amp = A.max(0)
    t = np.take_along_axis(np.array(trans), o[None], 0)[0]
    o = np.where(amp < wall, -1, o)

    def per_site(a):
        return np.repeat(a.ravel(), ns)
    return DomainMap(per_site(o), per_site(t), per_site(amp),
                     [frac_label(m, n)[4:] for m in star], wall)
