"""Draw the app icon and write packaging/icons/phase-tiles.{png,ico,icns}.

    python tools/make_icon.py

A 3 x 3 grid of Brillouin-zone hexagons, each a phase colour, with a
few dark Bragg spots.  The .icns needs macOS (iconutil); elsewhere it
is skipped and the committed one stays.
"""
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPolygonF

ICONS = Path(__file__).resolve().parent.parent / "packaging" / "icons"
COLOURS = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2",
           "#eeca3b", "#b279a2", "#ff9da6", "#9d755d"]
SPOTS = [(0, 0), (1, 1), (2, 2), (0, 2), (2, 0)]


def hexagon(cx, cy, r):
    return QPolygonF([QPointF(cx + r * math.cos(math.pi / 3 * k),
                              cy + r * math.sin(math.pi / 3 * k))
                      for k in range(6)])


def draw(size=1024):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    m = size * 0.06
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#f4f1ea"))
    p.drawRoundedRect(m, m, size - 2 * m, size - 2 * m,
                      size * 0.18, size * 0.18)
    cell = (size - 4 * m) / 3
    r = cell * 0.47
    for i in range(3):
        for j in range(3):
            cx = 2 * m + cell * (j + 0.5)
            cy = 2 * m + cell * (i + 0.5)
            p.setBrush(QColor(COLOURS[3 * i + j]))
            p.drawPolygon(hexagon(cx, cy, r))
            if (i, j) in SPOTS:
                p.setBrush(QColor("#1d1d1f"))
                p.drawEllipse(QPointF(cx, cy), r * 0.18, r * 0.18)
    p.end()
    return img


def main():
    QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    ICONS.mkdir(parents=True, exist_ok=True)
    img = draw()
    img.save(str(ICONS / "phase-tiles.png"))
    img.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation
               ).save(str(ICONS / "phase-tiles.ico"), "ICO")
    if shutil.which("iconutil"):
        with tempfile.TemporaryDirectory() as d:
            iconset = Path(d) / "phase-tiles.iconset"
            iconset.mkdir()
            for s in (16, 32, 128, 256, 512):
                for scale, suffix in ((1, ""), (2, "@2x")):
                    img.scaled(s * scale, s * scale, Qt.KeepAspectRatio,
                               Qt.SmoothTransformation).save(
                        str(iconset / f"icon_{s}x{s}{suffix}.png"))
            subprocess.run(["iconutil", "-c", "icns", str(iconset),
                            "-o", str(ICONS / "phase-tiles.icns")],
                           check=True)
    print("wrote", *sorted(p.name for p in ICONS.iterdir()))


if __name__ == "__main__":
    main()
