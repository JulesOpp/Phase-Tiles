"""Keep every test off the real machine.

App data, the result cache and QSettings go to a temp folder made
once per session; nothing a test does lands in the user's Library or
AppData.  Set before any phasetiles import so module-level lookups
see it.
"""
import atexit
import os
import shutil
import tempfile

import pytest

_APP_DATA = tempfile.mkdtemp(prefix="phasetiles-test-appdata-")
atexit.register(shutil.rmtree, _APP_DATA, ignore_errors=True)
os.environ["PHASETILES_APP_DATA"] = _APP_DATA
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")


def pytest_collection_modifyitems(config, items):
    for item in items:
        src = open(item.fspath, encoding="utf-8").read()
        if "phasetilesapp" in src or "PySide6" in src:
            item.add_marker(pytest.mark.gui)


@pytest.fixture
def app_data():
    return _APP_DATA
