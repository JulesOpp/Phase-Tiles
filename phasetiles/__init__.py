"""Phase Tiles core: tiled Ising phase diagrams on 2D nets.

Never import Qt from this package -- tests/test_no_qt_in_core.py
fails the suite if anything does, because the CLI, CI and notebooks
run it without a display.
"""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("phase-tiles")
except PackageNotFoundError:          # source tree without pip install
    __version__ = "0.0.0"
