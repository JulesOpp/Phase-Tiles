"""Regenerate the shipped sample: square J1-J2, T 0.5, 5 x 5 tiles,
n = 24.  Small (about 0.5 MB) because it ships in every installer
and --selftest opens it."""
import pathlib
import tempfile

from phasetiles import project, runner
from phasetiles.spec import Axis, MCSettings, default_spec
from phasetiles.store import ResultStore

OUT = (pathlib.Path(__file__).resolve().parent.parent / "phasetiles"
       / "data" / "samples" / "square_j1j2.phtiles")

def main():
    spec = default_spec().replace(
        x=Axis("J1", -1, 1, 0.5), y=Axis("J2", -1, 1, 0.5),
        mc=MCSettings(n=24, anneal=1000, equil=1000, snaps=5))
    with tempfile.TemporaryDirectory() as d:
        st = ResultStore(d)
        runner.run_tiles(spec, st, 2)
        project.save_project(OUT, spec, st)
    print("wrote", OUT, OUT.stat().st_size // 1024, "kB")


if __name__ == "__main__":
    main()
