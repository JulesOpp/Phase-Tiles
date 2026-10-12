"""Scattering of MC snapshots: sublattice correlations, the
average-cell (folded) intensity, and order parameters.

The tiles show total scattering (Bragg + diffuse): a ferromagnet's
Bragg peak at Gamma is what makes a ferro tile recognisable.  Order
parameters use subtract_mean=True so that peak does not count as
order at q = 0.
"""
import numpy as np


def correlations(lat, snaps, subtract_mean=False):
    """C[m1, m2, j, k] = <F_j F_k*> / N_sites over snapshots, F_j the
    FFT over cells of the spins on sublattice j."""
    n, ns = lat.n, lat.nsub
    C = 0.0
    for s in snaps:
        d = s.reshape(n, n, ns).astype(float)
        if subtract_mean:
            d -= d.mean()
        F = np.fft.fft2(d, axes=(0, 1))
        C = C + F[..., :, None] * F[..., None, :].conj()
    return C / (len(snaps) * lat.N)


def folded_intensity(C, net, qmax=3.0):
    """Average over reciprocal cells:
    I(q) = <|sum_j F_j e^{-2 pi i (q+G).r_j}|^2>_{|q+G| <= qmax} / N,
    qmax in cycles per RCSR length (edge length 1).  For one site per
    cell this is S(q) exactly."""
    n, ns = C.shape[0], C.shape[2]
    if ns == 1:
        return C[..., 0, 0].real
    B = np.linalg.inv(net.A).T
    gm = int(np.ceil(qmax / min(np.linalg.norm(B, axis=1)))) + 1
    G = np.array([(h, k) for h in range(-gm, gm + 1)
                  for k in range(-gm, gm + 1)
                  if np.linalg.norm(np.array([h, k]) @ B) <= qmax])
    m = np.arange(n) / n
    q = np.stack(np.meshgrid(m, m, indexing="ij"), -1)
    out = np.zeros((n, n))
    for g in G:
        ph = np.exp(-2j * np.pi * (q + g) @ net.frac.T)
        out += np.einsum("abj,abjk,abk->ab", ph, C, ph.conj()).real
    return out / len(G)


def order_params(C):
    """phi(q)^2 = sum_j C_jj(q) / n^2: 1 for full single-q order on
    every sublattice."""
    n = C.shape[0]
    return np.einsum("abjj->ab", C).real / (n * n)
