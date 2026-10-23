"""What a diagram is: net, Hamiltonian, two axes, fixed values, MC
settings and display options.  Frozen, so the undo stack can hold
old specs by reference, and hashable into the result-cache key.

validate() returns sentences for the setup dock; Run is enabled only
when there are no errors.  A step that does not divide the range is a
warning, not an error -- the last tile simply stops short -- because
refusing 0.3 steps on a -1..1 range would be pedantry.
"""
import dataclasses
import hashlib
import json
from dataclasses import dataclass

import numpy as np

from phasetiles.hamiltonian import Hamiltonian

MAX_TILES = 5000


@dataclass(frozen=True)
class Axis:
    symbol: str
    start: float
    stop: float
    step: float

    def count(self):
        """0 for a step <= 0, a reversed range or a NaN/inf (validate()
        says why);
        never a ZeroDivisionError from whoever asks first."""
        if (not np.isfinite([self.start, self.stop, self.step]).all()
                or not self.step > 0 or self.stop < self.start):
            return 0
        return int(np.floor((self.stop - self.start) / self.step
                            + 1e-6)) + 1

    def values(self):
        return np.round(self.start + self.step
                        * np.arange(self.count()), 10)


@dataclass(frozen=True)
class MCSettings:
    n: int | None = None
    anneal: int = 3000
    equil: int = 2000
    snaps: int = 10
    seed: int = 1


@dataclass(frozen=True)
class Display:
    centre: str = "gamma"        # "gamma" | "half"
    dyn: float = 2.5
    phi0: float = 0.3
    qmax: float = 3.0
    show_t0: bool = True


@dataclass(frozen=True)
class DiagramSpec:
    net: str
    hamiltonian: Hamiltonian
    x: Axis
    y: Axis
    fixed: tuple = ()
    mc: MCSettings = MCSettings()
    display: Display = Display()

    def replace(self, **kw):
        return dataclasses.replace(self, **kw)

    def fixed_dict(self):
        """Every symbol of the Hamiltonian not on an axis, default 0.
        Values for unticked terms stay in `fixed` (remembered for when
        the term is ticked again) but are not returned."""
        given = dict(self.fixed)
        return {s: float(given.get(s, 0.0))
                for s in self.hamiltonian.symbols()
                if s not in (self.x.symbol, self.y.symbol)}

    def params_at(self, x, y):
        p = self.fixed_dict()
        p[self.x.symbol] = float(x)
        p[self.y.symbol] = float(y)
        return dict(sorted(p.items()))

    def n_cells(self, nsub):
        if self.mc.n:
            return self.mc.n
        return max(12, 12 * int(round(48 / np.sqrt(nsub) / 12)))

    def validate(self):
        errors, warnings = [], []
        syms = self.hamiltonian.symbols()
        # the cap comes before any values(): J1=-1:1:1e-9 once built a
        # 16 GB array just to warn that the steps miss the stop
        over = self.x.count() * self.y.count() > MAX_TILES
        for ax in (self.x, self.y):
            if ax.symbol not in syms:
                errors.append(f"{ax.symbol} is not a term of this "
                              "Hamiltonian; tick it in the term table.")
            if not np.isfinite([ax.start, ax.stop, ax.step]).all():
                errors.append(f"{ax.symbol}: start, stop and step must "
                              "be numbers.")
                continue
            if ax.step <= 0:
                errors.append(f"{ax.symbol} step must be > 0.")
                continue
            if ax.stop < ax.start:
                errors.append(f"{ax.symbol}: start {ax.start:g} is "
                              f"above stop {ax.stop:g}.")
                continue
            if over:
                continue
            last = ax.values()[-1]
            if abs(last - ax.stop) > 1e-6 * max(1, abs(ax.stop)):
                warnings.append(f"{ax.symbol}: {ax.step:g} steps do "
                                f"not reach {ax.stop:g}; last tile at "
                                f"{last:g}.")
            if ax.symbol == "T" and ax.start <= 0:
                errors.append("T must be > 0 (start the T axis above"
                              " 0).")
        if self.x.symbol == self.y.symbol:
            errors.append("Both axes are on the same parameter.")
        if self.fixed_dict().get("T", 1.0) <= 0:
            errors.append("T must be > 0.")
        # zero equil/snaps once ended a run in ZeroDivisionError
        mc = self.mc
        if mc.n is not None and mc.n < 0:
            errors.append("Supercell n must be >= 0 (0 = automatic).")
        if mc.anneal < 0:
            errors.append("anneal steps must be >= 0.")
        if mc.equil < 1:
            errors.append("equil steps must be >= 1.")
        if mc.snaps < 1:
            errors.append("snaps must be >= 1.")
        if not errors:
            n = self.x.count() * self.y.count()
            if n > MAX_TILES:
                errors.append(f"{n} tiles is more than {MAX_TILES}; "
                              "use a larger step.")
        return errors, warnings

    def mc_key(self):
        """Hash of everything that changes an MC result (not display)."""
        d = {"net": self.net, "ham": self.hamiltonian.to_dict(),
             "mc": dataclasses.asdict(self.mc)}
        return hashlib.sha1(json.dumps(d, sort_keys=True)
                            .encode()).hexdigest()[:16]

    def to_json(self):
        d = dataclasses.asdict(self)
        d["hamiltonian"] = self.hamiltonian.to_dict()
        d["fixed"] = [list(kv) for kv in self.fixed]
        return json.dumps(d, indent=1)

    @classmethod
    def from_json(cls, s):
        d = json.loads(s)
        return cls(net=d["net"],
                   hamiltonian=Hamiltonian.from_dict(d["hamiltonian"]),
                   x=Axis(**d["x"]), y=Axis(**d["y"]),
                   fixed=tuple((k, float(v)) for k, v in d["fixed"]),
                   mc=MCSettings(**d["mc"]),
                   display=Display(**d["display"]))


def default_spec():
    """Square J1-J2 at T = 0.5: the diagram the prototype was checked
    on (Neel, stripe, ferro; boundaries J2 = +-J1/2)."""
    return DiagramSpec(net="sql", hamiltonian=Hamiltonian(),
                       x=Axis("J1", -1.0, 1.0, 0.1),
                       y=Axis("J2", -1.0, 1.0, 0.1),
                       fixed=(("H", 0.0), ("T", 0.5)))
