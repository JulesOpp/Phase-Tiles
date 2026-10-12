"""Preferences that outlive a session, in QSettings.

Tests redirect QSettings to a temp folder (conftest `window`), so
nothing here may cache a path at import time.
"""
from pathlib import Path

from PySide6.QtCore import QSettings

from phasetiles.store import default_root


class Settings:
    def __init__(self):
        self._q = QSettings(QSettings.Format.IniFormat,
                            QSettings.Scope.UserScope, "PhaseTiles",
                            "Phase Tiles")

    @property
    def workers(self):
        return int(self._q.value("run/workers", 2))

    @workers.setter
    def workers(self, v):
        self._q.setValue("run/workers", int(v))

    @property
    def rcsr_path(self):
        v = self._q.value("data/rcsr_path", "")
        return v or None

    @rcsr_path.setter
    def rcsr_path(self, v):
        self._q.setValue("data/rcsr_path", v or "")

    @property
    def cache_root(self):
        return Path(self._q.value("data/cache", str(default_root())))
