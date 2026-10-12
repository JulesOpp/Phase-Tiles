"""Wrap the built .app in a compressed, read-only DMG.

    python packaging/makedmg.py

Plain hdiutil, not create-dmg: create-dmg drives Finder over Apple
events, which a CI runner is not allowed to do.  The arch suffix
keeps the arm64 and x86_64 builds apart on one release page.
"""
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bundle  # noqa: E402

DIST = bundle.ROOT / "dist"


def main():
    app = DIST / f"{bundle.NAME}.app"
    if not app.is_dir():
        sys.exit(f"{app} not found; run pyinstaller first")
    out = DIST / (f"Phase-Tiles-{bundle.version()}-"
                  f"{platform.machine()}.dmg")
    subprocess.run(["hdiutil", "create", "-volname", bundle.NAME,
                    "-srcfolder", str(app), "-ov", "-format", "UDZO",
                    str(out)], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
