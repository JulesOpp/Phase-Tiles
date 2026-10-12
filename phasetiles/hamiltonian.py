"""Hamiltonians as data: a model name and the terms switched on.

The GUI's term table is this list: one row per term the model offers,
a check box for each, so a new model is a new MODELS entry, not a new
dialog.  Pair term k couples shell k of nets.Net.shells -- J1 the
edges, J2... the geometric shells beyond (see CLAUDE.md invariant).
"""
from dataclasses import dataclass, field

SHELL_LABELS = {1: "NN", 2: "NNN", 3: "NNNN", 4: "4th", 5: "5th",
                6: "6th"}


@dataclass(frozen=True)
class Term:
    kind: str                    # "pair" | "field"
    shell: int = 0

    @property
    def symbol(self):
        return "H" if self.kind == "field" else f"J{self.shell}"

    @property
    def label(self):
        if self.kind == "field":
            return "field"
        return SHELL_LABELS[self.shell]


MODELS = {"ising": [Term("pair", k) for k in range(1, 7)]
          + [Term("field")]}


@dataclass(frozen=True)
class Hamiltonian:
    model: str = "ising"
    terms: tuple = field(default=(Term("pair", 1), Term("pair", 2)))

    def symbols(self):
        return [t.symbol for t in self.terms] + ["T"]

    def nshell(self):
        return max([t.shell for t in self.terms if t.kind == "pair"],
                   default=1)

    def formula(self):
        parts = [f"{t.symbol} Σ_{t.label} sᵢsⱼ" if t.kind == "pair"
                 else f"{t.symbol} Σ sᵢ" for t in self.terms]
        return "E = −" + " − ".join(parts) if parts else "E = 0"

    def to_dict(self):
        return {"model": self.model,
                "terms": [[t.kind, t.shell] for t in self.terms]}

    @classmethod
    def from_dict(cls, d):
        return cls(d["model"], tuple(Term(k, s) for k, s in d["terms"]))


def default():
    return Hamiltonian()
