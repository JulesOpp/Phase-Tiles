"""Fail if any binary in the .app needs a newer macOS than we promise.

    python packaging/check_macos_min.py ["dist/Phase Tiles.app"]

A wheel built for the CI runner's macOS (numpy's macosx_14_0 build
links Accelerate's new LAPACK) loads there and in the selftest, then
dies on import on every older Mac -- with no window, because it fails
before Qt starts.  1.0 shipped like that; the selftest cannot see it,
since it runs on the runner's own macOS.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bundle  # noqa: E402

_MAGIC = {b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe"}


def _version(s):
    return tuple(int(p) for p in s.split("."))


def min_os(path):
    """Highest minimum macOS among the file's architectures, or None
    for a binary that states none."""
    out = subprocess.run(["otool", "-arch", "all", "-l", str(path)],
                         capture_output=True, text=True).stdout
    found, lines = [], out.splitlines()
    for i, line in enumerate(lines):
        cmd = line.strip()
        if cmd in ("cmd LC_BUILD_VERSION", "cmd LC_VERSION_MIN_MACOSX"):
            key = "minos" if cmd.endswith("BUILD_VERSION") else "version"
            for nxt in lines[i + 1:i + 6]:
                parts = nxt.split()
                if parts[:1] == [key]:
                    found.append(_version(parts[1]))
                    break
    return max(found) if found else None


def binaries(app):
    for p in sorted(Path(app).rglob("*")):
        if p.is_symlink() or not p.is_file():
            continue
        with open(p, "rb") as f:
            if f.read(4) in _MAGIC:
                yield p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    app = Path(argv[0] if argv else
               bundle.ROOT / "dist" / f"{bundle.NAME}.app")
    limit = _version(bundle.MACOS_MIN)
    found = list(binaries(app))
    if not found:
        # a wrong path must not read as "all binaries are fine"
        print(f"no binaries under {app}", file=sys.stderr)
        return 2
    bad = [(p, v) for p in found
           if (v := min_os(p)) is not None and v > limit]
    for p, v in bad:
        print(f"needs macOS {'.'.join(map(str, v))}: "
              f"{p.relative_to(app)}")
    if bad:
        print(f"{len(bad)} binaries need more than macOS "
              f"{bundle.MACOS_MIN}", file=sys.stderr)
        return 1
    print(f"every binary runs on macOS {bundle.MACOS_MIN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
