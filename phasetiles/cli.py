"""`phasetiles` -- the core without a window.

nets / info / run work with numpy and scipy alone.  render draws the
same picture the GUI exports, so it needs the gui extra; without it
it says so and exits 3 rather than raising ImportError.  It runs the
GUI package in a subprocess because the core never imports Qt, not
even lazily (test_no_qt_in_core.py).
"""
import argparse
import subprocess
import sys

from phasetiles import extras, nets, runner
from phasetiles.hamiltonian import MODELS, Hamiltonian
from phasetiles.spec import Axis, DiagramSpec, MCSettings
from phasetiles.store import ResultStore


def _spec(a):
    """ValueError naming the argument it could not read: a traceback
    is no answer to a typo on the command line."""
    axes = []
    for v in a.vary:
        try:
            k, r = v.split("=")
            lo, hi, st = (float(t) for t in r.split(":"))
        except ValueError:
            raise ValueError(f"--vary {v}: expected "
                             "NAME=start:stop:step") from None
        axes.append(Axis(k, lo, hi, st))
    fixed = []
    for f in a.fix:
        for kv in f.split(","):
            try:
                k, v = kv.split("=")
                fixed.append((k, float(v)))
            except ValueError:
                raise ValueError(f"--fix {kv}: expected "
                                 "NAME=value") from None
    used = ({ax.symbol for ax in axes}
            | {k for k, v in fixed if v != 0 and k != "T"})
    terms = tuple(t for t in MODELS[a.ham] if t.symbol in used)
    return DiagramSpec(a.net, Hamiltonian(a.ham, terms), axes[0],
                       axes[1], tuple(fixed),
                       MCSettings(a.n, a.anneal, a.equil, a.snaps,
                                  a.seed))


def main(argv=None):
    p = argparse.ArgumentParser(prog="phasetiles")
    p.add_argument("mode", choices=["nets", "info", "run", "render"])
    p.add_argument("--net", default="sql")
    p.add_argument("--ham", default="ising", choices=sorted(MODELS))
    p.add_argument("--vary", action="append", default=[],
                   help="NAME=start:stop:step (x first, then y)")
    p.add_argument("--fix", action="append", default=[],
                   help="NAME=value[,NAME=value]")
    p.add_argument("--n", type=int)
    p.add_argument("--anneal", type=int, default=3000)
    p.add_argument("--equil", type=int, default=2000)
    p.add_argument("--snaps", type=int, default=10)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--out", help="image file for render")
    a = p.parse_args(argv)
    if a.mode == "nets":
        for k, (g, nn) in sorted(nets.list_2d().items()):
            print(f"{k:<10} {g:<5} {nn} node orbit(s)")
        return 0
    if a.mode == "info":
        print(nets.Net(a.net, nshell=6).describe())
        return 0
    if len(a.vary) != 2:
        print("give two --vary NAME=start:stop:step", file=sys.stderr)
        return 2
    try:
        spec = _spec(a)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    errors, warnings = spec.validate()
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    if a.mode == "run":
        st = ResultStore()
        n = runner.run_tiles(spec, st, a.workers)
        print(f"{n} tiles computed into {st.root}")
        return 0
    if not extras.available("gui"):
        print("render " + extras.hint("gui"), file=sys.stderr)
        return 3
    return subprocess.call([sys.executable, "-m", "phasetilesapp.main",
                            "--render", spec.to_json(),
                            a.out or "diagram.png"])


if __name__ == "__main__":
    sys.exit(main())
