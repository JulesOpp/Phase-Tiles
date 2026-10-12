"""Undo for diagram specs, without Qt.

Every edit is a whole-spec replacement: specs are small frozen
dataclasses, so storing old and new is cheaper and simpler than
inverse operations, and undo can never drift out of sync.  "Clean"
is a position in the stack, not a flag, so undoing back to the save
point makes the document clean again.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SetSpec:
    old: object
    new: object
    text: str


class CommandStack:
    def __init__(self, spec):
        self._base = spec
        self._cmds = []
        self._index = 0
        self._clean = 0

    @property
    def current(self):
        if self._index:
            return self._cmds[self._index - 1].new
        return self._base

    def push(self, cmd):
        del self._cmds[self._index:]
        if self._clean > self._index:
            self._clean = -1          # the save point was discarded
        self._cmds.append(cmd)
        self._index += 1

    def undo(self):
        if self.can_undo:
            self._index -= 1

    def redo(self):
        if self.can_redo:
            self._index += 1

    @property
    def can_undo(self):
        return self._index > 0

    @property
    def can_redo(self):
        return self._index < len(self._cmds)

    @property
    def undo_text(self):
        return self._cmds[self._index - 1].text if self.can_undo else ""

    @property
    def redo_text(self):
        return self._cmds[self._index].text if self.can_redo else ""

    @property
    def is_clean(self):
        return self._index == self._clean

    def mark_clean(self):
        self._clean = self._index
