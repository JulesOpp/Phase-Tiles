"""2D nets from RCSR .cgd data: parse, expand by plane-group symmetry,
build interaction shells.

A net is a list of nodes (fractional x, y in the cell) and edges (node
i -> node j + lattice offset).  J1 couples the net's edges; Jn (n >= 2)
couples the (n-1)-th geometric distance shell beyond the edges (all
node pairs at one distance, within DTOL, form one shell) -- see the
CLAUDE.md invariant before changing that.  Centred groups (cm, c2mm)
keep the conventional cell, so the cell holds both centring copies.

The data is the shipped 2D extract (data/rcsr2d.cgd) unless
Preferences points set_source() at the user's own full file.
"""
import functools
import itertools

import numpy as np

from phasetiles import resources

TOL = 1e-3     # fractional tolerance for merging symmetry copies
DTOL = 1e-3    # distance tolerance (RCSR length units) for shells


def _m(*r):
    return np.array(r, float).reshape(2, 2)


# Plane-group generators (R, t) on fractional (x, y): x' = R x + t,
# ITA standard settings.
_I = _m(1, 0, 0, 1)
_2 = (_m(-1, 0, 0, -1), (0, 0))
_mx = (_m(-1, 0, 0, 1), (0, 0))                 # x -> -x
_4 = (_m(0, -1, 1, 0), (0, 0))                  # (x,y) -> (-y, x)
_3 = (_m(0, -1, 1, -1), (0, 0))                 # (x,y) -> (-y, x-y)
GENS = {
    "p1": [], "p2": [_2], "pm": [_mx], "pg": [(_mx[0], (0, .5))],
    "cm": [_mx], "p2mm": [_2, _mx], "p2mg": [_2, (_mx[0], (.5, 0))],
    "p2gg": [_2, (_mx[0], (.5, .5))], "c2mm": [_2, _mx],
    "p4": [_4], "p4mm": [_4, _mx], "p4gm": [_4, (_mx[0], (.5, .5))],
    "p3": [_3], "p3m1": [_3, (_m(0, -1, -1, 0), (0, 0))],
    "p31m": [_3, (_m(0, 1, 1, 0), (0, 0))],
    "p6": [_3, _2], "p6mm": [_3, _2, (_m(0, -1, -1, 0), (0, 0))],
}
CENTRED = {"cm", "c2mm"}
PLANE_GROUPS = ["p1", "p2", "pm", "pg", "cm", "p2mm", "p2mg", "p2gg",
                "c2mm", "p4", "p4mm", "p4gm", "p3", "p3m1", "p31m",
                "p6", "p6mm"]
COMMON = [("Square", "sql"), ("Triangular", "hxl"),
          ("Honeycomb", "hcb"), ("Kagome", "kgm")]

_SOURCE = None        # None: the shipped extract; else a user's file


def group_ops(g):
    """All operations (R, t mod 1) of plane group g, with centring."""
    ops = [(_I, np.zeros(2))]
    gens = [(R, np.array(t, float)) for R, t in GENS[g]]
    if g in CENTRED:
        gens.append((_I, np.array([.5, .5])))

    def key(R, t):
        return (tuple(R.ravel().astype(int)),
                tuple(np.round(t % 1, 6) % 1))
    seen = {key(*ops[0])}
    i = 0
    while i < len(ops):
        R1, t1 = ops[i]
        for R2, t2 in gens:
            R, t = R2 @ R1, (R2 @ t1 + t2) % 1
            k = key(R, t)
            if k not in seen:
                seen.add(k)
                ops.append((R, t))
        i += 1
    return ops


def set_source(path):
    """Preferences > RCSR file.  None restores the shipped extract."""
    global _SOURCE
    _SOURCE = path
    _parsed.cache_clear()


def _text():
    if _SOURCE is None:
        return resources.read_text("rcsr2d.cgd")
    with open(_SOURCE, encoding="utf-8") as f:
        return f.read()


def _parse(lines):
    """{name: dict(group, cell=(a, b, gamma), nodes, edges)}, 2D only."""
    nets, cur = {}, None
    for line in lines:
        w = line.split()
        if not w or w[0].startswith("#"):
            continue
        if w[0] == "CRYSTAL":
            cur = dict(nodes=[], edges=[])
        elif cur is None:
            continue
        elif w[0] == "NAME":
            cur["name"] = w[1]
        elif w[0] == "GROUP":
            cur["group"] = w[1]
        elif w[0] == "CELL":
            cur["cell"] = tuple(float(x) for x in w[1:])
        elif w[0] == "NODE":
            cur["nodes"].append((int(w[2]),
                                 tuple(float(x) for x in w[3:])))
        elif w[0] == "EDGE":
            v = [float(x) for x in w[1:]]
            cur["edges"].append((tuple(v[:len(v) // 2]),
                                 tuple(v[len(v) // 2:])))
        elif w[0] == "END":
            if ("name" in cur and cur.get("group") in GENS
                    and len(cur.get("cell", ())) == 3):
                nets[cur["name"]] = cur
            cur = None
    return nets


@functools.lru_cache(maxsize=1)
def _parsed():
    return _parse(_text().splitlines())


def read_cgd():
    return _parsed()


def list_2d():
    """{name: (plane group, number of node orbits)}."""
    return {k: (v["group"], len(v["nodes"]))
            for k, v in read_cgd().items()}


class Net:
    """Periodic 2D net: sites (fractional), basis A (rows = a, b in
    Cartesian), shells of bonds.

    shells[n] = list of (i, j, (di, dj)): site i in cell 0 bonded to
    site j in cell (di, dj); each bond once.
    """

    def __init__(self, name, nshell=6):
        d = read_cgd()[name]
        self.name, self.group = name, d["group"]
        a, b, gam = d["cell"]
        g = np.radians(gam)
        self.A = np.array([[a, 0.0], [b * np.cos(g), b * np.sin(g)]])
        self.ops = group_ops(self.group)
        sites, coord = [], []
        for cn, x in d["nodes"]:
            for R, t in self.ops:
                y = (R @ np.array(x) + t) % 1
                y[np.abs(y - 1) < TOL] = 0
                if not any(np.allclose(_wrap(y - s), 0, atol=TOL)
                           for s in sites):
                    sites.append(y)
                    coord.append(cn)
        self.frac = np.array(sites)
        self.coord = np.array(coord)
        self.nsub = len(sites)
        edges = set()
        for p, q in d["edges"]:
            for R, t in self.ops:
                i, ci = self._locate(R @ np.array(p) + t)
                j, cj = self._locate(R @ np.array(q) + t)
                edges.add(_canon(i, j, tuple(int(x) for x in cj - ci)))
        self.edges = sorted(edges)
        deg = np.zeros(self.nsub, int)
        for i, j, _ in self.edges:
            deg[i] += 1
            deg[j] += 1
        self.degree = deg
        self.shells = [self.edges] + self._geom_shells(nshell)

    def _locate(self, x):
        """Site index and integer cell of fractional point x."""
        for i, s in enumerate(self.frac):
            dlt = x - s
            if np.allclose(dlt, np.round(dlt), atol=TOL):
                return i, np.round(dlt).astype(int)
        raise ValueError(f"edge end {x} is not a node of {self.name}")

    def cart(self, i, off=(0, 0)):
        return (self.frac[i] + np.array(off)) @ self.A

    def bond_length(self, bond):
        i, j, off = bond
        return float(np.linalg.norm(self.cart(j, off) - self.cart(i)))

    def _geom_shells(self, nshell):
        """Distance shells of node pairs beyond the edges (first
        nshell - 1 of them)."""
        self.shell_dist = [self.bond_length(self.edges[0])]
        if nshell <= 1:
            return []
        eset = set(self.edges)
        L = 4
        pairs = {}
        for i, j in itertools.product(range(self.nsub), repeat=2):
            for off in itertools.product(range(-L, L + 1), repeat=2):
                if i == j and off == (0, 0):
                    continue
                c = _canon(i, j, off)
                if c in eset or c in pairs:
                    continue
                pairs[c] = np.linalg.norm(self.cart(j, off)
                                          - self.cart(i))
        levels = []
        for x in sorted(pairs.values()):
            if not levels or x - levels[-1] > DTOL:
                levels.append(x)
        out = [sorted(c for c, x in pairs.items() if abs(x - lev) <= DTOL)
               for lev in levels[:nshell - 1]]
        self.shell_dist += [float(x) for x in levels[:nshell - 1]]
        return out

    def shell_counts(self):
        """Neighbours per site in each shell, for the Hamiltonian
        table ("J2 . NNN . d = 1.414 . 4 neighbours")."""
        out = []
        for sh in self.shells:
            z = np.zeros(self.nsub, int)
            for i, j, _ in sh:
                z[i] += 1
                z[j] += 1
            out.append(z.tolist())
        return out

    def describe(self):
        lines = [f"net {self.name}  group {self.group}  {self.nsub} "
                 f"site(s)/cell  degree {self.degree.tolist()}"]
        rows = zip(self.shells, self.shell_dist, self.shell_counts(),
                   strict=True)
        for n, (sh, dd, z) in enumerate(rows):
            lines.append(f"  J{n + 1}  d = {dd:.4f}  bonds/cell "
                         f"{len(sh)}  neighbours/site {z}")
        return "\n".join(lines)


def _wrap(x):
    return x - np.round(x)


def _canon(i, j, off):
    """One representative of a bond and its reverse."""
    rev = (j, i, (-off[0], -off[1]))
    return min((i, j, tuple(off)), rev)
