"""`phase-tiles --selftest [OUT.png]`: does this build actually work?

Runs inside whatever it was built into, so CI gets a non-zero exit
from a broken bundle instead of a screenshot nobody looks at.  It
checks what breaks only in a bundle:
1. package data via importlib.resources (the RCSR extract, sample);
2. the process pool under spawn -- two fresh tiles through
   runner.run_tiles with 2 workers, which hangs or opens windows if
   freeze_support() is missing (CLAUDE.md invariant);
3. QPainter + QImage + PNG plugin -- the export path.
It never opens a dialog: a modal in CI is a hang, not a failure.
"""
import shutil
import sys
import tempfile
import traceback
from pathlib import Path


def run_selftest(out=None):
    tmp = None
    try:
        from PySide6.QtWidgets import QDialog, QMessageBox

        from phasetilesapp.application import app
        app()  # QPainter on a QImage needs one; main() made it already

        def refuse(*a, **k):
            raise RuntimeError("selftest reached a modal dialog")
        QDialog.exec = refuse
        for n in ("question", "warning", "critical", "information"):
            setattr(QMessageBox, n, staticmethod(refuse))

        from phasetiles import nets, resources, runner
        from phasetiles.spec import Axis, MCSettings
        from phasetiles.store import ResultStore
        from phasetilesapp.document import Document
        from phasetilesapp.export import export_image

        assert len(nets.list_2d()) == 199, "RCSR extract missing"
        tmp = Path(tempfile.mkdtemp(prefix="phasetiles-selftest-"))
        doc = Document(store_root=tmp / "cache")
        with resources.path("samples/square_j1j2.phtiles") as p:
            doc.open(p)
        assert runner.jobs_for(doc.spec, doc.store) == [], \
            "sample tiles did not load"
        fresh = doc.spec.replace(
            x=Axis("J1", -1, 1, 2.0), y=Axis("J2", 0, 0, 1.0),
            mc=MCSettings(n=12, anneal=50, equil=50, snaps=1))
        n = runner.run_tiles(fresh, ResultStore(tmp / "pool"), 2)
        assert n == 2, f"process pool computed {n} of 2 tiles"
        out = Path(out or Path(tempfile.gettempdir())
                   / "phasetiles-selftest.png")
        export_image(doc, out, 1200, 600)
        assert out.exists() and out.stat().st_size > 10000, \
            "image missing or empty"
        print("selftest passed", out)
        return 0
    except Exception:
        traceback.print_exc()
        print("selftest FAILED", file=sys.stderr)
        return 1
    finally:
        # two cached tiles per run, forever, in the user's temp folder
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
