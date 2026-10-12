"""One .npz per tile, keyed by what made it.

The key is spec.mc_key() (net, Hamiltonian, MC settings) plus the
tile's parameter values, so a cached tile can never be shown on a
diagram of another net or model, and undoing a change finds the old
tiles again.  An unreadable file is a missing tile, not an error: the
next run recomputes it.
"""
import hashlib
import os
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class TileResult:
    params: dict
    C: np.ndarray
    phi2: np.ndarray
    snap: np.ndarray
    drift: float
    absm: float
    energy: float


def default_root():
    env = os.environ.get("PHASETILES_APP_DATA")
    if env:
        return Path(env) / "cache"
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / "Phase Tiles" / "cache"


class ResultStore:
    def __init__(self, root=None):
        self.root = Path(root or default_root())

    def key(self, spec, params):
        # round then +0.0: -0.0 (which tile_centres can produce) and
        # tiny negatives must name the same file as 0.0
        p = ",".join(f"{k}={round(v, 6) + 0.0:+.6f}"
                     for k, v in sorted(params.items()))
        return hashlib.sha1(p.encode()).hexdigest()[:16]

    def _path(self, spec, params):
        return (self.root / spec.mc_key()
                / (self.key(spec, params) + ".npz"))

    def has(self, spec, params):
        return self._path(spec, params).exists()

    def get(self, spec, params):
        try:
            with np.load(self._path(spec, params),
                         allow_pickle=False) as z:
                return TileResult(params, z["C"], z["phi2"], z["snap"],
                                  float(z["drift"]), float(z["absm"]),
                                  float(z["energy"]))
        except (OSError, ValueError, KeyError, EOFError,
                zipfile.BadZipFile):
            return None

    def put(self, spec, params, r):
        f = self._path(spec, params)
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(f.stem + ".tmp.npz")
        np.savez_compressed(tmp, C=r.C.astype(np.complex64),
                            phi2=r.phi2, snap=r.snap, drift=r.drift,
                            absm=r.absm, energy=r.energy)
        os.replace(tmp, f)     # never a half-written tile on a crash

    def _tiles(self):
        # only <mc_key>/<tile>.npz: the cache folder is a preference
        # and may hold files the store did not write
        if not self.root.is_dir():
            return []
        return [p for p in self.root.glob("*/*.npz") if p.is_file()]

    def usage(self):
        """(tile files, bytes) on disk."""
        files = self._tiles()
        return len(files), sum(p.stat().st_size for p in files)

    def clear(self):
        """Delete every stored tile; returns how many.  Saved .phtiles
        projects carry their own tiles and are untouched."""
        files = self._tiles()
        for p in files:
            p.unlink(missing_ok=True)
        for d in {p.parent for p in files}:
            try:
                d.rmdir()           # only if nothing else is in it
            except OSError:
                pass
        return len(files)

    def files_for(self, spec):
        d = self.root / spec.mc_key()
        if not d.exists():
            return []
        return sorted(p for p in d.glob("*.npz")
                      if not p.name.endswith(".tmp.npz"))
