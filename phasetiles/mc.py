"""Metropolis Monte Carlo of the Ising model on an n x n supercell of
any 2D net (nets.Net).

E = -sum_k Jk sum_{<ij> in shell k} s_i s_j - H sum_i s_i
(J > 0 ferro, J < 0 antiferro; one atom per node).  Sites are coloured
greedily so no two interacting sites share a colour; each colour is
updated at once, which keeps detailed balance and lets numpy do a
whole colour per step.  Site index = (c1 n + c2) nsub + i for cell
(c1, c2) and sublattice i.
"""
from dataclasses import dataclass

import numpy as np
from scipy import sparse


class Cancelled(Exception):
    """Raised inside run_mc when should_stop() says so; the runner
    turns it into 'tile not computed', never into a stored result."""


@dataclass
class MCResult:
    snaps: np.ndarray
    energy: np.ndarray
    drift: float


class Lattice:
    def __init__(self, net, n, nshell):
        self.net, self.n, self.nsub = net, n, net.nsub
        self.N = n * n * net.nsub
        c1, c2 = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        c1, c2 = c1.ravel(), c2.ravel()

        def idx(a, b, i):
            return ((a % n) * n + (b % n)) * net.nsub + i
        self.adj = []
        for sh in net.shells[:nshell]:
            rows, cols = [], []
            for i, j, (d1, d2) in sh:
                p, q = idx(c1, c2, i), idx(c1 + d1, c2 + d2, j)
                rows += [p, q]
                cols += [q, p]
            r, c = np.concatenate(rows), np.concatenate(cols)
            self.adj.append(sparse.csr_matrix(
                (np.ones(len(r)), (r, c)), shape=(self.N, self.N)))
        self.colours = self._colour(sum(self.adj))

    def _colour(self, A):
        A = A.tocsr()
        col = -np.ones(self.N, int)
        for p in range(self.N):
            used = set(col[A.indices[A.indptr[p]:A.indptr[p + 1]]]
                       .tolist())
            c = 0
            while c in used:
                c += 1
            col[p] = c
        return [np.flatnonzero(col == c) for c in range(col.max() + 1)]

    def coupling(self, J):
        W = sparse.csr_matrix((self.N, self.N))
        for Jk, A in zip(J, self.adj, strict=False):
            if Jk:
                W = W + Jk * A
        return W.tocsr()


def run_mc(lat, J, H, T, n_anneal, n_equil, n_snap, seed,
           should_stop=None):
    """Anneal geometrically from 5 max(|J|, |H|, T) to T, then
    equilibrate at T.  Snapshots are int8 (n_snap, N); drift is
    |<E>_last third - <E>_middle third| / |<E>| of the equilibration."""
    rng = np.random.default_rng(seed)
    W = lat.coupling(J)
    Wc = [W[c] for c in lat.colours]
    s = rng.choice(np.array([-1.0, 1.0]), size=lat.N)
    T0 = 5 * max(max(abs(x) for x in J), abs(H), T)
    temps = np.concatenate([
        np.geomspace(T0, T, n_anneal) if n_anneal else np.empty(0),
        np.full(n_equil, T)])
    every = max(n_equil // max(n_snap, 1), 1)
    snaps, e = [], np.empty(len(temps))
    for t, Tt in enumerate(temps):
        if should_stop is not None and t % 50 == 0 and should_stop():
            raise Cancelled()
        for c, Wk in zip(lat.colours, Wc, strict=True):
            dE = 2.0 * s[c] * (Wk @ s + H)
            acc = (dE <= 0) | (rng.random(len(c))
                               < np.exp(-np.clip(dE, 0, None) / Tt))
            s[c[acc]] *= -1
        e[t] = (-0.5 * s @ (W @ s) - H * s.sum()) / lat.N
        k = t - n_anneal
        if k >= 0 and (k + 1) % every == 0 and len(snaps) < n_snap:
            snaps.append(s.astype(np.int8))
    eq = e[n_anneal:]
    th = max(len(eq) // 3, 1)
    drift = 0.0
    if len(eq) >= 2 * th:
        last = eq[-th:].mean()
        drift = abs(last - eq[-2 * th:-th].mean()) / max(abs(last),
                                                          1e-12)
    return MCResult(np.array(snaps), e, float(drift))
