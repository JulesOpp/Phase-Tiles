"""The selected tile in real space: its last MC snapshot as spins,
or labelled into orientation and antiphase domains (core
domains.domain_map).  The view is a factory argument so widget tests
can inject a stub (CLAUDE.md, testing)."""
import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from phasetiles import classify, domains
from phasetilesapp.diagram_painter import CYCLE

WALL = QColor(220, 220, 220)


class DomainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pos = np.zeros((0, 2))
        self.cols = []
        self.zoom = 1.0
        self.setMinimumSize(320, 320)

    def widget(self):
        return self

    def set_data(self, pos, colours, cell):
        self.pos, self.cols = pos, colours
        self.update()

    def wheelEvent(self, ev):
        f = 1.15 if ev.angleDelta().y() > 0 else 1 / 1.15
        self.zoom = float(np.clip(self.zoom * f, 1, 12))
        self.update()

    def paintEvent(self, ev):
        if not len(self.pos):
            return
        lo, hi = self.pos.min(0), self.pos.max(0)
        span = np.maximum(hi - lo, 1e-9)
        k = self.zoom * 0.95 * min(self.width() / span[0],
                                   self.height() / span[1])
        mid = (lo + hi) / 2
        r = max(1.5, 0.42 * k * self._spacing())
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for v, c in zip(self.pos, self.cols, strict=True):
            p.setBrush(c)
            p.drawEllipse(QPointF(self.width() / 2 + (v[0] - mid[0]) * k,
                                  self.height() / 2
                                  - (v[1] - mid[1]) * k), r, r)
        p.end()

    def _spacing(self):
        d = np.linalg.norm(self.pos[1:50] - self.pos[0], axis=1)
        return float(d[d > 1e-9].min()) if (d > 1e-9).any() else 1.0


def _swatch(colour):
    return f'<span style="color:{QColor(colour).name()}">■</span>'


class DomainsPanel(QDockWidget):
    def __init__(self, doc, make_view=None, parent=None):
        super().__init__("Domains", parent)
        self.doc = doc
        body = QWidget()
        v = QVBoxLayout(body)
        self.mode = QComboBox()
        self.mode.addItems(["Spins", "Domains"])
        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setTextFormat(Qt.TextFormat.PlainText)
        self.legend = QLabel()
        self.legend.setWordWrap(True)
        self.legend.setTextFormat(Qt.TextFormat.RichText)
        self.view = (make_view or DomainView)()
        v.addWidget(self.mode)
        v.addWidget(self.view.widget(), 1)
        v.addWidget(self.info)
        v.addWidget(self.legend)
        self.setWidget(body)
        self.mode.currentTextChanged.connect(self.refresh)
        doc.selectionChanged.connect(self.refresh)
        doc.tilesChanged.connect(self.refresh)
        doc.specChanged.connect(self.refresh)
        self.refresh()

    def _clear(self, text):
        self.info.setText(text)
        self.view.set_data(np.zeros((0, 2)), [], None)

    def refresh(self, *_):
        t = self.doc.selected
        self.legend.setText("")
        if t is None:
            return self._clear("Click a tile to see its domains.")
        s, net = self.doc.spec, self.doc.net
        p = s.params_at(t.x, t.y)
        head = ", ".join(f"{k} = {v:g}" for k, v in p.items())
        r = self.doc.tile_result(t)
        if r is None:
            return self._clear(f"{head} — not computed yet "
                               "(Run ▸ Run).")
        n = s.n_cells(net.nsub)
        ph = classify.classify(r.phi2, r.absm, n,
                               classify.canonical_q(net, n),
                               s.display.phi0, net.nsub)
        self.info.setText(
            f"{head}\n{ph.label} · φ = {ph.amplitude:.2f} · "
            f"|m| = {r.absm:.2f} · drift {r.drift:.3f} · "
            f"E/site {r.energy:.3f}")
        pos = domains.site_positions(net, n)
        if self.mode.currentText() == "Spins" or not ph.star:
            up, dn = self.palette().highlight().color(), QColor(150, 150,
                                                                150)
            cols = [up if x > 0 else dn for x in r.snap]
            if self.mode.currentText() == "Domains":
                self.legend.setText("disordered: no domains to label")
        else:
            dm = domains.domain_map(net, n, r.snap,
                                    r.C.astype(complex), ph.star)
            cols = [WALL if o < 0
                    else QColor(CYCLE[o % len(CYCLE)]).lighter(
                        100 + 45 * int(tr))
                    for o, tr in zip(dm.orientation, dm.translation,
                                     strict=True)]
            self.legend.setText(" · ".join(
                f"{_swatch(CYCLE[i % len(CYCLE)])} q = {nm}"
                for i, nm in enumerate(dm.names))
                + f" · lighter = antiphase · {_swatch(WALL)} wall")
        self.view.set_data(pos, cols, net.A)
