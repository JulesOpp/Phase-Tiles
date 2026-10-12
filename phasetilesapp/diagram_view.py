"""The diagram as a widget: paints DiagramPainter, rebuilds the model
only when the document changes, and turns clicks into selection."""
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from phasetilesapp.diagram_painter import DiagramModel, DiagramPainter


class DiagramView(QWidget):
    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.painter = DiagramPainter()
        self._model = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setMinimumSize(360, 300)
        for sig in (doc.specChanged, doc.tilesChanged):
            sig.connect(self.invalidate)
        doc.selectionChanged.connect(lambda *_: self.update())

    def invalidate(self, *_):
        self._model = None
        self.update()

    def model(self):
        if self._model is None:
            self._model = DiagramModel.build(self.doc)
        return self._model

    def paintEvent(self, ev):
        p = QPainter(self)
        self.painter.paint(p, self.rect().toRectF(), self.model(),
                           self.palette(), self.doc.selected)
        p.end()

    def mousePressEvent(self, ev):
        self.doc.select(self.painter.hit(self.rect().toRectF(),
                                         self.model(),
                                         ev.position()))
