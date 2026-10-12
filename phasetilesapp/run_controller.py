"""Runs the missing tiles off the GUI thread.

The runner itself is the core's (process pool); this only moves it
to a QThread and turns its callbacks into throttled signals, so a
441-tile run repaints twice a second, not 441 times.  The spec is
captured at start: editing during a run never mixes two diagrams.
"""
import threading

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from phasetiles import runner


class _Worker(QThread):
    tile = Signal()
    done = Signal(int, bool)

    def __init__(self, spec, store, workers, stop):
        super().__init__()
        self.spec, self.store, self.workers = spec, store, workers
        self._stop = stop

    def run(self):
        n = runner.run_tiles(self.spec, self.store, self.workers,
                             on_tile=lambda r: self.tile.emit(),
                             should_stop=self._stop.is_set)
        self.done.emit(n, self._stop.is_set())


class RunController(QObject):
    started = Signal(int)
    progress = Signal(int, int)
    finished = Signal(int, bool)

    def __init__(self, doc, workers=2, parent=None):
        super().__init__(parent)
        self.doc, self.workers = doc, workers
        self._thread = None
        self._stop = threading.Event()
        self._done = self._total = 0
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self.doc.notify_tiles)

    def is_running(self):
        return self._thread is not None and self._thread.isRunning()

    def start(self):
        if self.is_running():
            return
        spec = self.doc.spec
        self._total = len(runner.jobs_for(spec, self.doc.store))
        self._done = 0
        self._stop.clear()
        self._thread = _Worker(spec, self.doc.store, self.workers,
                               self._stop)
        self._thread.tile.connect(self._on_tile)
        self._thread.done.connect(self._on_done)
        self.started.emit(self._total)
        self._timer.start()
        self._thread.start()

    def stop(self):
        self._stop.set()

    def stop_and_wait(self, ms=30000):
        """Stop and block until the pool has shut down, for closing
        the window: an orphaned pool keeps computing after exit."""
        self.stop()
        if self._thread is not None:
            self._thread.wait(ms)

    def _on_tile(self):
        self._done += 1
        self.progress.emit(self._done, self._total)

    def _on_done(self, n, stopped):
        self._timer.stop()
        if self._thread is not None:
            self._thread.wait()
            self._thread = None
        self.doc.notify_tiles()
        self.finished.emit(n, stopped)
