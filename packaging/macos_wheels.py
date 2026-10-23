"""Swap numpy and scipy for their wheels built for bundle.MACOS_MIN.

    python packaging/macos_wheels.py      # before pyinstaller, macOS

pip picks the newest wheel the *build* machine accepts: on a macOS 14
runner that is numpy's and scipy's macosx_14_0 build (Accelerate's
new LAPACK), which cannot load on macOS 13 or older.  The same
versions are reinstalled from the wheels tagged for MACOS_MIN, so
the bundle runs everywhere Qt does.  check_macos_min.py verifies it.
"""
import platform
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bundle  # noqa: E402

PACKAGES = ["numpy", "scipy"]


def main():
    plat = (f"macosx_{bundle.MACOS_MIN.replace('.', '_')}_"
            f"{platform.machine()}")
    pins = [f"{p}=={version(p)}" for p in PACKAGES]
    pip = [sys.executable, "-m", "pip"]
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(pip + [
            "download", "--only-binary=:all:", "--no-deps",
            "--platform", plat, "--implementation", "cp",
            "--python-version",
            f"{sys.version_info.major}.{sys.version_info.minor}",
            "-d", d, *pins], check=True)
        wheels = sorted(str(p) for p in Path(d).glob("*.whl"))
        print("\n".join(Path(w).name for w in wheels))
        subprocess.run(pip + ["install", "--force-reinstall",
                              "--no-deps", *wheels], check=True)


if __name__ == "__main__":
    main()
