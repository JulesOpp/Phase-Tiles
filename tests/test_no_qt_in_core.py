"""The core must import without Qt: the CLI, CI's headless job and
notebooks all rely on it, and one stray import would make PySide6 a
hard dependency without anyone noticing."""
import ast
import pathlib

CORE = pathlib.Path(__file__).resolve().parent.parent / "phasetiles"


def test_no_core_module_imports_qt():
    bad = []
    for f in CORE.rglob("*.py"):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            bad += [f"{f.name}: {n}" for n in names
                    if n.split(".")[0] in ("PySide6", "PyQt5",
                                           "PyQt6", "phasetilesapp")]
    assert bad == []
