"""Optional features, checked without importing them.

find_spec, never import: importing PySide6 to ask whether it exists
costs a second and loads Qt into processes (the CLI, MC workers) that
must stay headless.
"""
import importlib.util

EXTRAS = {"gui": ("PySide6", "pip install 'phase-tiles[gui]'")}


def available(name):
    return importlib.util.find_spec(EXTRAS[name][0]) is not None


def hint(name):
    return f"needs the '{name}' extra: {EXTRAS[name][1]}"
