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
# No window may reach the screen, on a laptop or a headless CI runner.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def pytest_collection_modifyitems(config, items):
    for item in items:
        src = open(item.fspath, encoding="utf-8").read()
        # A test that only takes the `window` fixture mentions no Qt
        # name but still builds widgets, so it needs the modal guard.
        if ("phasetilesapp" in src or "PySide6" in src
                or "window" in getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.gui)


@pytest.fixture
def app_data():
    return _APP_DATA


@pytest.fixture(autouse=True)
def _no_modals(request, monkeypatch):
    """Reaching a modal is a failure, not a hang (see CLAUDE.md)."""
    if "gui" not in request.keywords:
        return
    from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

    def refuse(*a, **k):
        raise AssertionError("a modal would wait for a click")
    monkeypatch.setattr(QDialog, "exec", refuse)
    for name in ("question", "warning", "critical", "information",
                 "about"):
        monkeypatch.setattr(QMessageBox, name,
                            staticmethod(refuse))
    for name in ("getSaveFileName", "getOpenFileName"):
        monkeypatch.setattr(QFileDialog, name, staticmethod(refuse))


@pytest.fixture
def window(qtbot, tmp_path):
    """A main window that is never drawn on screen and is deleted
    when the test ends, with its settings in tmp_path."""
    from PySide6.QtCore import QSettings, Qt
    QSettings.setPath(QSettings.Format.IniFormat,
                      QSettings.Scope.UserScope, str(tmp_path))
    from phasetilesapp.mainwindow import MainWindow
    made = []

    def make(**kw):
        w = MainWindow(**kw)
        w.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        # pytest-qt closes its widgets before this fixture's teardown,
        # so the "discard changes?" guard must be cleared here.
        qtbot.addWidget(w, before_close_func=lambda w:
                        w.doc.stack.mark_clean())
        made.append(w)
        return w
    yield make
    for w in made:
        w.doc.stack.mark_clean()     # no "save changes?" on teardown
        w.close()
        w.deleteLater()
