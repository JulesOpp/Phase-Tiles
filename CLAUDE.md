# Phase Tiles

Tiled Ising phase diagrams on any 2D RCSR net: each tile is one Monte
Carlo run, drawn as its average-cell scattering folded into one
Brillouin zone; click a tile to see its domains.

## Layout
| Package | What it is |
|---|---|
| `phasetiles/` | Headless core. **Imports no Qt** (`test_no_qt_in_core.py`): the CLI, CI and notebooks run it without a display. |
| `phasetiles/data/` | Package data, read only through `phasetiles.resources.path()` so a checkout and a bundle find it the same way. |
| `phasetilesapp/` | PySide6 shell. Holds no physics; asks the core. |
| `phasetilesapp/document.py` | `Document`: the spec, its undo stack and the result store. Widgets never edit a spec; they call `Document.set_spec`. |
| `packaging/` | `bundle.py` (contents, both OSes), `macos.spec`, `windows.spec`, `.iss`, `makedmg.py`. |

## Commands
```bash
python -m pytest -q                 # everything
python -m pytest -q -m "not gui"    # core only, no display needed
ruff check .                        # lint; NEVER ruff format
phasetiles run --net sql --vary J1=-1:1:0.1 --vary J2=-1:1:0.1 --fix T=0.5
phase-tiles                         # GUI
phase-tiles --selftest out.png      # what CI runs in the bundle
pyinstaller --noconfirm packaging/macos.spec   # or windows.spec
```

## Conventions
- Line length 79, hand-formatted; `ruff check` only -- `ruff format`
  fights the layout.
- Comments and docstrings say *why* (the failure avoided), not what.
- Test names are sentences about behaviour.
- `@pytest.mark.slow` on anything taking seconds; keep MC grids in
  tests tiny (n <= 24, <= 9 tiles) -- the dev machine has 16 GB.

## Invariants (product decisions -- do not undo)
- **Core never imports Qt.** Why: headless CLI/CI/notebooks.
- **Every spec change goes through `Document.set_spec`** (one undo
  step). Why: undo, scripting and tests without a window.
- **Results are keyed by (net, Hamiltonian, MC settings, parameter
  values)**, never by position in the grid. Why: changing the net or
  the range must not show another diagram's tiles, and undo must find
  the old tiles again.
- **Display options never trigger MC.** Tile centre, log decades,
  phase threshold, qmax re-render from stored correlations. Why: they
  are instant and runs take minutes.
- **J1 = the net's edges; Jk (k >= 2) = geometric distance shells
  beyond them.** Why: it reproduces the textbook J1-J2 square model
  and is defined for every RCSR net; changing it silently changes
  every saved diagram.
- **Tiles are Wigner-Seitz cells laid on the reciprocal lattice**, so
  they tile exactly; the (1/2,1/2) centre moves the content only.
- **`multiprocessing.freeze_support()` is the first call in
  `phasetilesapp.main.main`.** Why: in a frozen build every spawned
  worker re-runs the app; without it each worker opens a window.
- **Data is read through `importlib.resources` only, no `sys.frozen`
  branches**, and `bundle.py` must name every file in
  `resources.REQUIRED` (`test_packaging.py`).
- **No plotting library.** Diagram, legend, net preview and domains
  are QPainter, following the palette.
- **Tests never wait on a modal** (conftest makes them raise) and
  never write outside the temp app-data.
- **Default MC workers = 2.** Why: 16 GB machines; more workers swap.
