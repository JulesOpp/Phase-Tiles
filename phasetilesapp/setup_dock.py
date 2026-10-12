"""Everything that defines a diagram, in one dock: topology,
Hamiltonian, the two axes, MC settings, and the validation sentences
that decide whether Run is enabled."""
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from phasetiles import nets
from phasetiles.spec import Axis, MCSettings
from phasetilesapp.collapsible import Section, fixed_dock, scrolling
from phasetilesapp.hamiltonian_editor import HamiltonianEditor
from phasetilesapp.net_preview import NetPreview


def _dspin(lo=-100, hi=100, step=0.1):
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(4)
    s.setSingleStep(step)
    return s


class SetupDock(QDockWidget):
    def __init__(self, doc, parent=None):
        super().__init__("Diagram", parent)
        self.doc = doc
        self.ok = True
        body = QWidget()
        v = QVBoxLayout(body)
        # topology
        gb = Section("Topology")
        f = QFormLayout(gb.body)
        self.family = QComboBox()
        self.family.addItem("Common")
        groups = {g for g, _ in nets.list_2d().values()}
        for g in nets.PLANE_GROUPS:
            if g in groups:
                self.family.addItem(g)
        self.net = QComboBox()
        self.preview = NetPreview()
        self.net_info = QLabel()
        f.addRow("Family", self.family)
        f.addRow("Net", self.net)
        f.addRow(self.preview)
        f.addRow(self.net_info)
        v.addWidget(gb)
        # hamiltonian
        gb = Section("Hamiltonian (J > 0 ferro)")
        lay = QVBoxLayout(gb.body)
        self.ham = HamiltonianEditor(doc)
        lay.addWidget(self.ham)
        v.addWidget(gb)
        # axes
        gb = Section("Varied parameters")
        f = QFormLayout(gb.body)
        self.x_sym, self.y_sym = QComboBox(), QComboBox()
        self.x_start, self.x_stop, self.x_step = (_dspin(), _dspin(),
                                                  _dspin(1e-4, 100, .01))
        self.y_start, self.y_stop, self.y_step = (_dspin(), _dspin(),
                                                  _dspin(1e-4, 100, .01))
        for lab, sym, a, b, c in (
                ("X", self.x_sym, self.x_start, self.x_stop,
                 self.x_step),
                ("Y", self.y_sym, self.y_start, self.y_stop,
                 self.y_step)):
            # symbol on its own line: one seven-widget row set the
            # dock's minimum width, and so the window's
            f.addRow(lab, sym)
            row = QHBoxLayout()
            for wdg in (QLabel("from"), a, QLabel("to"), b,
                        QLabel("step"), c):
                row.addWidget(wdg)
            f.addRow("", row)
        v.addWidget(gb)
        # MC
        gb = Section("Monte Carlo")
        f = QFormLayout(gb.body)
        self.mc_n = QSpinBox()
        self.mc_n.setRange(0, 192)
        self.mc_n.setSingleStep(12)
        self.mc_n.setSpecialValueText("auto")
        self.mc_anneal, self.mc_equil = QSpinBox(), QSpinBox()
        self.mc_snaps, self.mc_seed = QSpinBox(), QSpinBox()
        for s_, hi in ((self.mc_anneal, 100000),
                       (self.mc_equil, 100000), (self.mc_snaps, 100),
                       (self.mc_seed, 10 ** 6)):
            s_.setRange(1, hi)
        f.addRow("Cells (n × n)", self.mc_n)
        f.addRow("Anneal sweeps", self.mc_anneal)
        f.addRow("Equilibration sweeps", self.mc_equil)
        f.addRow("Snapshots", self.mc_snaps)
        f.addRow("Seed", self.mc_seed)
        v.addWidget(gb)
        self.messages = QLabel()
        self.messages.setWordWrap(True)
        self.messages.setTextFormat(Qt.TextFormat.PlainText)
        v.addWidget(self.messages)
        v.addStretch(1)
        self.setWidget(scrolling(body))
        fixed_dock(self)
        # wiring: each user edit -> one set_spec
        self.family.currentTextChanged.connect(self._fill_nets)
        self.net.currentIndexChanged.connect(self._net_chosen)
        for w in (self.x_start, self.x_stop, self.x_step, self.y_start,
                  self.y_stop, self.y_step):
            w.editingFinished.connect(self._axes_edited)
        self.x_sym.activated.connect(self._axes_edited)
        self.y_sym.activated.connect(self._axes_edited)
        for w in (self.mc_n, self.mc_anneal, self.mc_equil,
                  self.mc_snaps, self.mc_seed):
            w.editingFinished.connect(self._mc_edited)
        self.ham.refused.connect(self.messages.setText)
        doc.specChanged.connect(self.populate)
        self.populate()

    def _fill_nets(self, family):
        b = QSignalBlocker(self.net)
        self.net.clear()
        if family == "Common":
            for label, key in nets.COMMON:
                self.net.addItem(f"{label} ({key})", key)
        else:
            for k, (g, _) in sorted(nets.list_2d().items()):
                if g == family:
                    self.net.addItem(k, k)
        # -1 when the current net is not in this family: nothing is
        # chosen until the user picks, so browsing families is free.
        self.net.setCurrentIndex(self.net.findData(self.doc.spec.net))
        b.unblock()

    def _net_chosen(self, *_):
        key = self.net.currentData()
        if key and key != self.doc.spec.net:
            self.doc.set_spec(self.doc.spec.replace(net=key),
                              f"Net {key}")

    def _axes_edited(self, *_):
        s = self.doc.spec
        x = Axis(self.x_sym.currentText(), self.x_start.value(),
                 self.x_stop.value(), self.x_step.value())
        y = Axis(self.y_sym.currentText(), self.y_start.value(),
                 self.y_stop.value(), self.y_step.value())
        if (x, y) != (s.x, s.y):
            self.doc.set_spec(s.replace(x=x, y=y), "Axes")

    def _mc_edited(self):
        s = self.doc.spec
        mc = MCSettings(self.mc_n.value() or None,
                        self.mc_anneal.value(), self.mc_equil.value(),
                        self.mc_snaps.value(), self.mc_seed.value())
        if mc != s.mc:
            self.doc.set_spec(s.replace(mc=mc), "Monte Carlo settings")

    def populate(self, *_):
        s, net = self.doc.spec, self.doc.net
        common = {k for _, k in nets.COMMON}
        fam = "Common" if s.net in common else net.group
        b = QSignalBlocker(self.family)
        self.family.setCurrentText(fam)
        b.unblock()
        self._fill_nets(fam)
        self.preview.set_net(net)
        self.net_info.setText(
            f"{net.group} · {net.nsub} site(s)/cell · coordination "
            f"{'/'.join(map(str, sorted(set(net.coord.tolist()))))}")
        syms = s.hamiltonian.symbols()
        for combo, ax, a, b_, c in (
                (self.x_sym, s.x, self.x_start, self.x_stop,
                 self.x_step),
                (self.y_sym, s.y, self.y_start, self.y_stop,
                 self.y_step)):
            blockers = [QSignalBlocker(w) for w in (combo, a, b_, c)]
            combo.clear()
            combo.addItems(syms if ax.symbol in syms
                           else syms + [ax.symbol])
            combo.setCurrentText(ax.symbol)
            a.setValue(ax.start)
            b_.setValue(ax.stop)
            c.setValue(ax.step)
            for bl in blockers:
                bl.unblock()
        for w, val in ((self.mc_n, s.mc.n or 0),
                       (self.mc_anneal, s.mc.anneal),
                       (self.mc_equil, s.mc.equil),
                       (self.mc_snaps, s.mc.snaps),
                       (self.mc_seed, s.mc.seed)):
            bl = QSignalBlocker(w)
            w.setValue(val)
            bl.unblock()
        errors, warnings = s.validate()
        self.ok = not errors
        n = s.x.count() * s.y.count() if self.ok else 0
        self.messages.setText("\n".join(
            errors + warnings
            + ([f"{n} tiles · {s.n_cells(net.nsub)}² cells"]
               if self.ok else [])))
