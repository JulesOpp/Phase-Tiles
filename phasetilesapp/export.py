"""File > Export Image: the same DiagramPainter the window uses,
onto a QImage (PNG/JPEG) or an SVG, in a light palette so a figure
exported from a dark-theme session still prints."""
from pathlib import Path

from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPalette
from PySide6.QtSvg import QSvgGenerator

from phasetilesapp.diagram_painter import DiagramModel, DiagramPainter


def light_palette():
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor("white"))
    p.setColor(QPalette.ColorRole.WindowText, QColor("black"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#2a78d6"))
    return p


def export_image(doc, path, width=2400, height=1150, palette=None):
    path = Path(path)
    model = DiagramModel.build(doc)
    pal = palette or light_palette()
    rect = QRectF(0, 0, width, height)
    if path.suffix.lower() == ".svg":
        gen = QSvgGenerator()
        gen.setFileName(str(path))
        gen.setSize(QSize(width, height))
        gen.setViewBox(rect)
        gen.setTitle("Phase Tiles diagram")
        p = QPainter(gen)
        DiagramPainter().paint(p, rect, model, pal)
        p.end()
        return path
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    DiagramPainter().paint(p, rect, model, pal)
    p.end()
    if not img.save(str(path)):
        raise OSError(f"could not write {path}")
    return path


def render_spec(spec_json, out):
    from phasetiles import runner
    from phasetiles.spec import DiagramSpec
    from phasetilesapp.document import Document
    from phasetilesapp.settings import Settings
    st = Settings()
    doc = Document(DiagramSpec.from_json(spec_json),
                   store_root=st.cache_root)
    runner.run_tiles(doc.spec, doc.store, st.workers)
    export_image(doc, out)
    print("wrote", out)
    return 0
