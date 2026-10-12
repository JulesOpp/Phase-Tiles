"""A small drawing of the selected net so the drop-down name has a
picture: 3 x 3 cells, edges then sites, centred and scaled to fit."""
import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget


class NetPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.net = None
        self.setMinimumSize(180, 140)

    def set_net(self, net):
        self.net = net
        self.update()

    def paintEvent(self, ev):
        if self.net is None:
            return
        net = self.net
        cells = [(i, j) for i in range(-1, 2) for j in range(-1, 2)]
        pts = np.array([(np.array(c) + f) @ net.A
                        for c in cells for f in net.frac])
        lo, hi = pts.min(0), pts.max(0)
        k = 0.85 * min(self.width() / (hi - lo)[0],
                       self.height() / (hi - lo)[1])
        mid = (lo + hi) / 2

        def to(v):
            return QPointF(self.width() / 2 + (v[0] - mid[0]) * k,
                           self.height() / 2 - (v[1] - mid[1]) * k)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(self.palette().windowText().color(), 1.2))
        for c in cells:
            for i, j, off in net.edges:
                a = net.cart(i, c)
                b = net.cart(j, (c[0] + off[0], c[1] + off[1]))
                p.drawLine(to(a), to(b))
        p.setBrush(self.palette().highlight())
        p.setPen(Qt.PenStyle.NoPen)
        for v in pts:
            p.drawEllipse(to(v), 3.5, 3.5)
        p.end()
