"""The Hamiltonian as a term table: one row per term the model
offers (J1 NN, J2 NNN, J3 NNNN, ... H field), each ticked on or off,
with the shell distance and neighbour count for the current net, and
the fixed value used when the term is not on an axis.  T is a
permanent row.  The live formula underneath is what the diagram
title will say."""
from dataclasses import dataclass

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QWidget,
)

from phasetiles.hamiltonian import MODELS, Hamiltonian


@dataclass
class Row:
    check: QCheckBox
    info: QLabel
    value: QDoubleSpinBox


class HamiltonianEditor(QWidget):
    refused = Signal(str)

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.doc = doc
        g = QGridLayout(self)
        self.rows = {}
        terms = MODELS[doc.spec.hamiltonian.model]
        for r, t in enumerate(terms + [None]):
            sym = "T" if t is None else t.symbol
            name = ("T  temperature" if t is None
                    else f"{t.symbol}  {t.label}")
            cb = QCheckBox(name)
            if t is None:
                cb.setChecked(True)
                cb.setEnabled(False)
            info = QLabel()
            val = QDoubleSpinBox()
            val.setRange(-100, 100)
            val.setDecimals(4)
            val.setSingleStep(0.05)
            g.addWidget(cb, r, 0)
            g.addWidget(info, r, 1)
            g.addWidget(val, r, 2)
            self.rows[sym] = Row(cb, info, val)
            if t is not None:
                cb.toggled.connect(lambda on, t=t: self._toggle(t, on))
            val.editingFinished.connect(lambda s=sym: self._value(s))
        self.formula = QLabel()
        self.formula.setWordWrap(True)
        g.addWidget(self.formula, len(self.rows), 0, 1, 3)
        doc.specChanged.connect(self.populate)
        self.populate()

    def populate(self, *_):
        s, net = self.doc.spec, self.doc.net
        on = set(s.hamiltonian.symbols())
        fixed = dict(s.fixed)
        counts = net.shell_counts()
        axes = {s.x.symbol: "X axis", s.y.symbol: "Y axis"}
        for sym, row in self.rows.items():
            bc, bv = QSignalBlocker(row.check), QSignalBlocker(row.value)
            if sym != "T":
                row.check.setChecked(sym in on)
            row.info.setText("")
            if sym.startswith("J"):
                k = int(sym[1:]) - 1
                if k < len(counts) and k < len(net.shell_dist):
                    z = sorted(set(counts[k]))
                    row.info.setText(
                        f"d = {net.shell_dist[k]:.3f} · "
                        f"{'/'.join(map(str, z))} neighbours")
                else:
                    row.info.setText("no such shell")
            elif sym == "H":
                row.info.setText("uniform field")
            row.value.setValue(fixed.get(sym, 0.0))
            row.value.setEnabled(sym in on and sym not in axes)
            if sym in axes:
                row.info.setText(row.info.text() + " · " + axes[sym])
            bc.unblock()
            bv.unblock()
        self.formula.setText(s.hamiltonian.formula())

    def _toggle(self, term, on):
        s = self.doc.spec
        if not on and term.symbol in (s.x.symbol, s.y.symbol):
            axis = "X" if term.symbol == s.x.symbol else "Y"
            self.populate()
            self.refused.emit(f"{term.symbol} is on the {axis} axis; "
                              "move the axis first.")
            return
        order = MODELS[s.hamiltonian.model]
        cur = set(s.hamiltonian.terms)
        cur = cur | {term} if on else cur - {term}
        ham = Hamiltonian(s.hamiltonian.model,
                          tuple(t for t in order if t in cur))
        self.doc.set_spec(s.replace(hamiltonian=ham),
                          f"{'Add' if on else 'Remove'} {term.symbol}")

    def _value(self, sym):
        s = self.doc.spec
        v = self.rows[sym].value.value()
        fixed = dict(s.fixed)
        if fixed.get(sym, 0.0) == v:
            return
        fixed[sym] = v
        self.doc.set_spec(s.replace(fixed=tuple(sorted(fixed.items()))),
                          f"{sym} = {v:g}")
