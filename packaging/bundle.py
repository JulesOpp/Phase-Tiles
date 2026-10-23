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
COPYRIGHT = "Copyright (c) 2026 Jules Oppenheim, MIT License"
# Qt 6.9 needs 12.0 and scipy's oldest arm64 wheel 12.3 (its
# gfortran); CI installs numpy/scipy wheels built for this, and
# check_macos_min.py holds every binary in the .app to it.
MACOS_MIN = "12.3"

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


# Their licences must travel with their code (BSD notice clauses,
# LGPL for Qt).  PySide6 wheels carry no licence file, so its texts
# are in packaging/licenses/.
NOTICE_PACKAGES = ["numpy", "scipy"]


def licence_datas():
    """(src, dest) pairs for licenses/ in the bundle: ours, the
    notices index, Qt's LGPL/GPL, CPython's and each wheel's own."""
    import sys  # noqa: PLC0415
    from importlib.metadata import distribution  # noqa: PLC0415
    lic = HERE / "licenses"
    out = [(str(ROOT / "LICENSE"), "licenses"),
           (str(lic / "THIRD-PARTY-NOTICES.txt"), "licenses"),
           (str(lic / "LGPL-3.0.txt"), "licenses/qt"),
           (str(lic / "GPL-3.0.txt"), "licenses/qt")]
    base = Path(sys.base_prefix)
    for p in (base / "LICENSE.txt",
              base / "lib" / f"python{sys.version_info.major}."
              f"{sys.version_info.minor}" / "LICENSE.txt"):
        if p.is_file():
            out.append((str(p), "licenses/python"))
            break
    for pkg in NOTICE_PACKAGES:
        dist = distribution(pkg)
        for f in dist.files or []:
            if any(k in f.name.upper()
                   for k in ("LICENSE", "COPYING", "NOTICE")):
                rel = Path(f).parent.as_posix()
                out.append((str(f.locate()), f"licenses/{pkg}/{rel}"))
    return out


def version():
    from importlib.metadata import version as v
    return v("phase-tiles")


def windows_version():
    parts = [int(p) for p in version().split(".")[:3]
             if p.isdigit()]
    return tuple((parts + [0, 0, 0, 0])[:4])
