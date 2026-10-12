"""What goes in the bundle, for both platforms.

macos.spec and windows.spec differ only in Info.plist/.icns against a
version resource/.ico; the contents are here, so a forgotten data
file is one fix, not two.  project_datas(), EXCLUDES and
HIDDEN_IMPORTS are plain data over pathlib because
tests/test_packaging.py imports this module in the ordinary suite,
without PyInstaller.

Data lands at _internal/phasetiles/data/..., where
importlib.resources finds it in a onedir bundle exactly as on a
checkout -- no sys.frozen branch anywhere (CLAUDE.md invariant).
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ICONS = HERE / "icons"
NAME = "Phase Tiles"

# spawn workers import these by name; PyInstaller's analysis cannot
# see a pickled function's module.
HIDDEN_IMPORTS = ["phasetiles.runner", "phasetiles.mc",
                  "phasetiles.scattering", "scipy.spatial._qhull",
                  "scipy.ndimage"]

# Never needed and each tens of MB if a transitive import drags them.
EXCLUDES = ["matplotlib", "tkinter", "pytest", "IPython", "PyQt5",
            "PyQt6", "PySide6.Qt3DCore", "PySide6.QtWebEngineCore",
            "PySide6.QtMultimedia", "PySide6.QtQuick"]


def project_datas():
    from phasetiles import resources  # noqa: PLC0415
    data = ROOT / "phasetiles" / "data"
    out = []
    for name in resources.REQUIRED:
        src = data / name
        dest = (Path("phasetiles/data") / name).parent.as_posix()
        out.append((str(src), dest))
    out.append((str(data / "PROVENANCE.md"), "phasetiles/data"))
    return out


def version():
    from importlib.metadata import version as v
    return v("phase-tiles")


def windows_version():
    parts = [int(p) for p in version().split(".")[:3]
             if p.isdigit()]
    return tuple((parts + [0, 0, 0, 0])[:4])
