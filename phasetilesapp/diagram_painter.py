"""The diagram, drawn with QPainter: panel (a) tile images, panel
(b) phase colours, T = 0 boundaries on both, axes and a legend.

Painting is separate from the widget so File > Export Image and
--selftest draw exactly what the window shows, onto a QImage or an
SVG, with no plotting library (CLAUDE.md invariant).
"""
from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPainterPath,
    QPen,
    QPolygonF,
)

from phasetiles import classify, groundstate, render, scattering, tiling

PHASE_COLOURS = {"ferro (q = 0)": "#e8c547", "disordered": "#dcdbd6"}
CYCLE = ["#2a78d6", "#eb6834", "#1baf7a", "#7d5cc6", "#c2185b",
         "#00838f", "#8d6e63", "#5c6bc0", "#9e9d24", "#d84315",
         "#26a69a", "#ab47bc"]
NPX = 81


@dataclass
class Tile:
    centre: tiling.TileCentre
    poly: np.ndarray            # parameter coordinates
    array: np.ndarray | None    # 0..1, NaN outside
    image: QImage | None
    phase: classify.Phase | None
    extent: tuple               # param-coord bbox of the image


def _qimage(a):
    """0 = white .. 1 = black, transparent outside the tile; row 0 of
    `a` is the lowest q_y, row 0 of a QImage is the top."""
    a = np.flipud(a)
    g = np.nan_to_num(255 * (1 - a), nan=255).astype(np.uint8)
    alpha = np.where(np.isnan(a), 0, 255).astype(np.uint8)
    rgba = np.dstack([g, g, g, alpha]).copy()
    h, w = g.shape
    return QImage(rgba.data, w, h, 4 * w,
                  QImage.Format.Format_RGBA8888).copy()


# Rendered tiles by (store, MC settings, parameters, display look).
# Results never change once stored, so during a run a rebuild only
# renders the new tiles (a full 441-tile render is ~2 s; it happens
# every 500 ms while tiles arrive).  ~80 kB per entry.
_TILES = {}
_TILES_MAX = 1024
_SEGMENTS = {}


def _remember(cache, key, value, cap):
    if len(cache) >= cap:
        cache.pop(next(iter(cache)))
    cache[key] = value


def _render_tile(r, net, poly, n, qlab, d):
    inten = scattering.folded_intensity(r.C.astype(complex), net, d.qmax)
    arr, qext = render.tile_image(inten, net, poly, d.centre, NPX, d.dyn)
    ph = classify.classify(r.phi2, r.absm, n, qlab, d.phi0, net.nsub)
    return arr, _qimage(arr), ph, qext


@dataclass
class DiagramModel:
    tiles: list
    segments: np.ndarray
    t0_note: str | None
    legend: list                 # [(label, colour, count)]
    colours: dict
    bounds: tuple
    aspect: float                # y-unit length / x-unit length
    title: str
    xlabel: str
    ylabel: str

    @classmethod
    def build(cls, doc):
        s, net = doc.spec, doc.net
        n = s.n_cells(net.nsub)
        B, poly = tiling.recip(net)
        mx, my = tiling.scale(B, s.x, s.y)
        qlab = classify.canonical_q(net, n)
        tiles, colours, counts = [], dict(PHASE_COLOURS), {}
        d = s.display
        look = (d.centre, d.dyn, d.phi0, d.qmax)
        for c in tiling.tile_centres(B, s.x, s.y):
            p = s.params_at(c.x, c.y)
            tp = tiling.tile_polygon(poly, mx, my, c.x, c.y)
            key = (str(doc.store.root), s.mc_key(),
                   doc.store.key(s, p), look)
            hit = _TILES.get(key)
            if hit is None:
                r = doc.store.get(s, p)
                if r is None:
                    tiles.append(Tile(c, tp, None, None, None, ()))
                    continue
                hit = _render_tile(r, net, poly, n, qlab, d)
                _remember(_TILES, key, hit, _TILES_MAX)
            arr, img, ph, (qx0, qx1, qy0, qy1) = hit
            if ph.label not in colours:
                colours[ph.label] = CYCLE[(len(colours) - 2)
                                          % len(CYCLE)]
            counts[ph.label] = counts.get(ph.label, 0) + 1
            ext = (c.x + qx0 * mx, c.x + qx1 * mx,
                   c.y + qy0 * my, c.y + qy1 * my)
            tiles.append(Tile(c, tp, arr, img, ph, ext))
        note = groundstate.unavailable_reason(s, net)
        seg = np.zeros((0, 2, 2))
        if note is None and s.display.show_t0:
            gkey = (s.net, s.hamiltonian, tuple(s.fixed_dict().items()),
                    s.x, s.y)
            if gkey not in _SEGMENTS:
                bs = groundstate.sums(net, s.hamiltonian.nshell())
                _remember(_SEGMENTS, gkey, None if bs is None else
                          groundstate.segments(
                              *groundstate.label_grid(bs, s)), 16)
            seg = _SEGMENTS[gkey]
            if seg is None:
                note = "T = 0 lines unavailable for this net."
                seg = np.zeros((0, 2, 2))
        legend = sorted(((k, colours[k], v) for k, v in counts.items()),
                        key=lambda e: (e[0] not in PHASE_COLOURS,
                                       -e[2]))
        fx = ", ".join(f"{k} = {v:g}" for k, v in s.fixed_dict().items())
        title = (f"{net.name} ({net.group}, {net.nsub} site"
                 f"{'s' if net.nsub > 1 else ''}/cell) · "
                 f"{s.hamiltonian.formula()} · {fx} · {n}×{n} cells")
        return cls(tiles, seg, note, legend, colours,
                   tiling.bounds(s.x, s.y), mx / my, title,
                   s.x.symbol, s.y.symbol)


class DiagramPainter:
    """Two square-ish panels side by side, legend to the right of (b).
    Margins in pixels; everything else scales with the rect."""
    LEFT, BOTTOM, TOP, GAP, LEGEND = 56, 44, 52, 48, 210

    def panels(self, rect, model):
        w = rect.width() - self.LEFT * 2 - self.GAP - self.LEGEND
        h = rect.height() - self.TOP - self.BOTTOM
        x0, x1, y0, y1 = model.bounds
        # keep the BZ undistorted: pixel per y-unit = aspect * per x
        kx = max(1e-6, min(w / 2 / (x1 - x0),
                           h / ((y1 - y0) * model.aspect)))
        pw, ph = kx * (x1 - x0), kx * model.aspect * (y1 - y0)
        top = rect.top() + self.TOP + (h - ph) / 2
        a = QRectF(rect.left() + self.LEFT, top, pw, ph)
        b = QRectF(a.right() + self.GAP + self.LEFT, top, pw, ph)
        return a, b

    def to_widget(self, rect, model, panel, x, y):
        pa = self.panels(rect, model)[panel]
        x0, x1, y0, y1 = model.bounds
        return QPointF(pa.left() + (x - x0) / (x1 - x0) * pa.width(),
                       pa.bottom() - (y - y0) / (y1 - y0) * pa.height())

    def _poly(self, rect, model, panel, pts):
        return QPolygonF([self.to_widget(rect, model, panel, *p)
                          for p in pts])

    def hit(self, rect, model, pos):
        for panel in (0, 1):
            for t in model.tiles:
                if self._poly(rect, model, panel, t.poly).containsPoint(
                        pos, Qt.FillRule.OddEvenFill):
                    return t.centre
        return None

    def paint(self, p, rect, model, palette, selected=None):
        p.save()
        p.fillRect(rect, palette.window())
        p.setRenderHint(p.RenderHint.Antialiasing)
        p.setRenderHint(p.RenderHint.SmoothPixmapTransform)
        fg = palette.windowText().color()
        a, b = self.panels(rect, model)
        for panel, pr in ((0, a), (1, b)):
            p.save()
            p.setClipRect(pr)
            for t in model.tiles:
                poly = self._poly(rect, model, panel, t.poly)
                path = QPainterPath()
                path.addPolygon(poly)
                if panel == 0 and t.image is not None:
                    tl = self.to_widget(rect, model, 0, t.extent[0],
                                        t.extent[3])
                    br = self.to_widget(rect, model, 0, t.extent[1],
                                        t.extent[2])
                    p.save()
                    p.setClipPath(path, Qt.ClipOperation.IntersectClip)
                    p.drawImage(QRectF(tl, br), t.image)
                    p.restore()
                elif panel == 1 and t.phase is not None:
                    col = QColor(model.colours[t.phase.label])
                    col.setAlphaF(0.35 + 0.65 * min(t.phase.amplitude,
                                                    1.0))
                    p.fillPath(path, col)
                else:
                    p.fillPath(path, QColor(128, 128, 128, 40))
                p.setPen(QPen(QColor(180, 180, 180), 0.5))
                p.drawPolygon(poly)
            # selection last, so neighbours' outlines don't cover it
            for t in model.tiles:
                if selected is not None and t.centre == selected:
                    p.setPen(QPen(palette.highlight().color(), 2.5))
                    p.drawPolygon(self._poly(rect, model, panel, t.poly))
            p.setPen(QPen(fg, 1.4))
            for (u, v) in model.segments:
                p.drawLine(self.to_widget(rect, model, panel, *u),
                           self.to_widget(rect, model, panel, *v))
            p.restore()
            self._axes(p, rect, model, panel, pr, fg)
        self._titles(p, rect, model, a, b, fg)
        self._legend(p, b, model, fg)
        p.restore()

    def _axes(self, p, rect, model, panel, pr, fg):
        p.setPen(QPen(fg, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(pr)
        x0, x1, y0, y1 = model.bounds
        fm = p.fontMetrics()
        for v in _ticks(x0, x1):
            q = self.to_widget(rect, model, panel, v, y0)
            p.drawLine(q, q + QPointF(0, 4))
            s = f"{v:g}"
            p.drawText(QPointF(q.x() - fm.horizontalAdvance(s) / 2,
                               q.y() + 6 + fm.ascent()), s)
        for v in _ticks(y0, y1):
            q = self.to_widget(rect, model, panel, x0, v)
            p.drawLine(q, q - QPointF(4, 0))
            s = f"{v:g}"
            p.drawText(QPointF(q.x() - 7 - fm.horizontalAdvance(s),
                               q.y() + fm.ascent() / 2 - 1), s)
        p.drawText(QRectF(pr.left(), pr.bottom() + 6 + fm.height(),
                          pr.width(), fm.height() + 4),
                   Qt.AlignmentFlag.AlignHCenter, model.xlabel)
        p.save()
        p.translate(pr.left() - self.LEFT + 4, pr.center().y())
        p.rotate(-90)
        p.drawText(QRectF(-pr.height() / 2, 0, pr.height(),
                          fm.height() + 2),
                   Qt.AlignmentFlag.AlignHCenter, model.ylabel)
        p.restore()

    def _titles(self, p, rect, model, a, b, fg):
        p.setPen(fg)
        fm = p.fontMetrics()
        p.drawText(QRectF(rect.left() + 8, rect.top() + 6,
                          rect.width() - 16, fm.height() + 4),
                   Qt.AlignmentFlag.AlignHCenter
                   | Qt.TextFlag.TextSingleLine, model.title)
        for pr, s in ((a, "(a) average-cell scattering, per-tile log"),
                      (b, "(b) phase from order parameters")):
            p.drawText(QRectF(pr.left(), pr.top() - fm.height() - 6,
                              pr.width() + self.LEGEND, fm.height() + 4),
                       Qt.AlignmentFlag.AlignLeft, s)
        if model.t0_note:
            f = QFont(p.font())
            f.setItalic(True)
            p.save()
            p.setFont(f)
            p.drawText(QRectF(b.left(), b.bottom() + 8 + 2 * fm.height(),
                              b.width() + self.LEGEND, fm.height() + 4),
                       Qt.AlignmentFlag.AlignLeft, model.t0_note)
            p.restore()

    def _legend(self, p, b, model, fg):
        fm = p.fontMetrics()
        x, y = b.right() + 16, b.top() + 2
        p.setPen(fg)
        p.drawText(QPointF(x, y + fm.ascent()), "phase (opacity = order)")
        y += fm.height() + 8
        sw = fm.height() - 2
        for label, colour, count in model.legend:
            p.fillRect(QRectF(x, y, sw, sw), QColor(colour))
            p.setPen(QPen(fg, 0.5))
            p.drawRect(QRectF(x, y, sw, sw))
            # multi-q labels can be longer than the legend column
            text = fm.elidedText(f"{label} ({count})",
                                 Qt.TextElideMode.ElideMiddle,
                                 int(self.LEGEND - sw - 26))
            p.drawText(QPointF(x + sw + 8, y + fm.ascent() - 1), text)
            y += fm.height() + 4


def _ticks(lo, hi, k=5):
    """About k round values inside [lo, hi]: the bounds sit half a
    step outside the grid, so linspace over them prints 1.25, -0.75."""
    raw = (hi - lo) / k
    mag = 10 ** np.floor(np.log10(raw))
    step = mag * min((1, 2, 2.5, 5, 10), key=lambda m: abs(m * mag - raw))
    first = np.ceil(lo / step - 1e-9) * step
    return [round(v, 10) for v in np.arange(first, hi + 1e-9, step)]
