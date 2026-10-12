"""The one open diagram: its spec, undo history and results.

Widgets never hold a spec of their own and never edit one; they call
set_spec() and listen to specChanged.  That single funnel is what
makes every edit undoable and testable without a window.
"Modified" is a position in the undo stack, so undoing to the save
point is clean again.
"""
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from phasetiles import nets, project
from phasetiles.commands import CommandStack, SetSpec
from phasetiles.spec import default_spec
from phasetiles.store import ResultStore


class Document(QObject):
    specChanged = Signal(object, object)
    tilesChanged = Signal()
    modifiedChanged = Signal(bool)
    selectionChanged = Signal(object)

    def __init__(self, spec=None, store_root=None, parent=None):
        super().__init__(parent)
        self.stack = CommandStack(spec or default_spec())
        self.store = ResultStore(store_root)
        self.path = None
        self.selected = None
        self._net = None

    spec = property(lambda self: self.stack.current)
    modified = property(lambda self: not self.stack.is_clean)

    @property
    def net(self):
        if self._net is None or self._net.name != self.spec.net:
            self._net = nets.Net(self.spec.net, nshell=6)
        return self._net

    def _changed(self, old):
        new = self.spec
        if (new.net, new.x, new.y) != (old.net, old.x, old.y):
            self.select(None)
        self.specChanged.emit(new, old)
        self.modifiedChanged.emit(self.modified)

    def set_spec(self, new, text):
        old = self.spec
        if new == old:
            return
        self.stack.push(SetSpec(old, new, text))
        self._changed(old)

    def undo(self):
        old = self.spec
        self.stack.undo()
        self._changed(old)

    def redo(self):
        old = self.spec
        self.stack.redo()
        self._changed(old)

    def select(self, tile):
        self.selected = tile
        self.selectionChanged.emit(tile)

    def tile_result(self, tile):
        if tile is None:
            return None
        return self.store.get(self.spec,
                              self.spec.params_at(tile.x, tile.y))

    def notify_tiles(self):
        self.tilesChanged.emit()

    def _reset(self, spec, path):
        old = self.spec
        self.stack = CommandStack(spec)
        self.path = Path(path) if path else None
        self._changed(old)
        self.tilesChanged.emit()

    def open_new(self):
        self._reset(default_spec(), None)

    def open(self, path):
        self._reset(project.load_project(path, self.store), path)

    def save(self, path=None):
        self.path = Path(path or self.path)
        project.save_project(self.path, self.spec, self.store)
        self.stack.mark_clean()
        self.modifiedChanged.emit(False)
