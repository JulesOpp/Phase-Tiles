"""Every data file the application reads, by name.

All reads go through here so a source checkout and a PyInstaller
bundle find files the same way (importlib.resources, no sys.frozen
branch), and so tests/test_packaging.py can hold bundle.py to the
list below: a file read but not bundled is a build that works on the
developer's machine and nowhere else.
"""
from contextlib import contextmanager
from importlib import resources

REQUIRED = (
    "rcsr2d.cgd",
    "samples/square_j1j2.phtiles",
)


def _ref(name):
    ref = resources.files("phasetiles") / "data"
    for part in name.split("/"):
        ref = ref / part
    return ref


def read_text(name):
    return _ref(name).read_text(encoding="utf-8")


@contextmanager
def path(name):
    with resources.as_file(_ref(name)) as p:
        yield p
