# Phase Tiles: design decisions and known limits

The decisions taken while building Phase Tiles (October 2026), each with what it would cost if wrong, and the review findings left for later. The invariants that must not be undone are in CLAUDE.md. Task numbers refer to the original build plan, which is not kept in the repository.

## Rulings

- No separate spec file: authority = user request quoted in plan "Requirements" + Global Constraints + the original research prototype. Rulings are provisional against that.
- Setup: Ruling: repo initialised on main with only the plan committed; all work on branch build/app — skill forbids implementing on main without consent — cost if wrong: one merge.
- Setup: Ruling: dev env is ~/GitHub/Phase-Tiles/.venv (python.org 3.12), not a system python — matches CI python 3.12 — cost if wrong: none.
- Setup: Ruling: milestones per user: M1 = Tasks 1–7 (core), M2 = 8–13 (GUI), M3 = 14–15 (ship); stop + handoff at each.
- - T8 MainWindow._refresh uses self.setup/self.running added in T10/T11 — plan T10 says to create them before first _refresh; T8 must not reference them. Ruling at T8: _refresh guards with getattr.
- Task 1: Ruling: added extend-exclude .superpowers to ruff config — ledger dir is not code — cost: none.
- Task 2: Ruling: rcsr2d.cgd is 100 kB, not the plan's ~60 kB estimate — content is exactly the 199 2D blocks — cost: none.
- Task 3: Ruling: params_at test expects no H (H unticked in default Hamiltonian), per plan's own note; test uses Display() directly and np.isclose for 0.8 — float stability — cost: none.
- Task 4: Ruling: variables named I renamed (ruff E741 ambiguous name) here and in later tasks' plan code — lint rule in Global Constraints — cost: none.
- Task 5: Ruling: classify._star returns only exact symmetry images (QLab.exact), not merged neighbour q's — plan's _star would have fed broadened neighbours to domains — cost if wrong: none (test unchanged).
- Task 5: Ruling: groundstate.label_grid prunes states to the convex hull of (u, v, c0) energy coefficients and sums() dedupes with np.unique — 5 s → 0.01 s per diagram build; exactness pinned by test_hull_pruning_matches_brute_force_with_a_field — cost if wrong: wrong T=0 lines (test guards).
- Task 5: Ruling: groundstate._value removed (folded into _coefficients) — internal only.
- Task 6: Ruling: added test_honeycomb_neel_is_one_domain_without_walls — the plan's tests only covered one-site nets; the eigenvector weighting is the multi-sublattice claim — cost: none.
- Task 7: Ruling: runner pool loop refills one job per finished tile (plan refilled one per wait) and stop drops running tiles via shutdown(cancel_futures) instead of storing them — no partial results either way; simpler — cost if wrong: a stopped run discards up to `workers` nearly-done tiles.
- Task 7: Ruling: load_project only writes tiles/<key>/<file>.npz and rejects '..' (zip-slip) — a .phtiles from someone else must not write outside the cache — test_a_project_cannot_write_outside_the_cache, mutation-checked — cost: none.
- Task 7: Ruling: CLI render uses a subprocess from the start (plan's inline correction); added tests for default_root env var, pool==serial snapshots, CLI run — cost: none.
- Task 8: Ruling: conftest marks tests that use the `window` fixture as gui (test_mainwindow.py names no Qt module, so the modal guard would not apply) and sets QT_QPA_PLATFORM=offscreen by default — cost: none.
- Task 8: Ruling: window fixture clears the clean state via qtbot.addWidget(before_close_func=) — pytest-qt closes widgets before fixture teardown, so the plan's teardown mark_clean came too late and closeEvent hit the modal guard — cost: none.
- Task 8: Ruling: open()/open_new() share Document._reset; _set_display uses dataclasses.replace — same behaviour, less code — cost: none.
- Task 9: Ruling: window fixture left as in Task 8 (plain MainWindow(**kw)); make_domain_view is passed by tests that need it — the brief's conftest note asked for nothing the fixture lacked — cost: none.
- Task 9: Ruling: test_clicking_a_tile_selects_it maps with v.rect().toRectF() (brief: v.rect()) — paint/hit use QRectF, QRect.bottom() is 1 px off — cost: none.
- Task 9: Ruling: axis ticks are round values (_ticks: 1/2/2.5/5 × 10^k) instead of np.linspace over the bounds — bounds sit half a step outside the grid, so linspace printed -1.25, -0.625 … — cost: none.
- Task 9: Ruling: selected outline drawn after all tiles; legend labels elided to the legend column (multi-q labels ran off the image at 1400 px) — found in the Step 7 visual check — cost: none.
- Task 9: Ruling: DiagramModel._cache not added — build time not yet measured on a big grid; measure in Task 11 — cost: possible sluggish redraw on 441-tile grids.
- Task 10: Ruling: net combo wired to currentIndexChanged only (plan also wired activated) — the plan's own Step 6 fallback; one signal per pick — cost: none.
- Task 10: Ruling: HamiltonianEditor._value compares with fixed.get(sym, 0.0) — fixed_dict defaults absent symbols to 0, so leaving a 0 field would otherwise push a no-op undo step — cost: none.
- Task 10: Ruling: J rows say "no such shell" when the net has fewer than k shells; QSignalBlockers are unblocked explicitly, not via del/with — cost: none.
- Task 10: Ruling: pre-flight getattr guard in _refresh not needed — setup dock and self.running are created before the first _refresh — cost: none.
- Task 11: Ruling: added RunController.stop_and_wait and test_closing_during_a_run_stops_it_first — plan said closeEvent waits for finished; a blocking QThread.wait is simpler and the mutant (no wait) aborts with "QThread destroyed while running" — cost: close can block up to 30 s during a long tile.
- Task 11: Ruling (core bug fix): ResultStore.key normalises round(v, 6) + 0.0 — tile_centres yields J2 = -0.0 for some columns and '{v:+.6f}' made -0.0 and 0.0 different files, so a lookup with 0.0 missed a computed tile; test_minus_zero_and_zero_are_the_same_tile RED→GREEN — cost: cache entries written before this fix with a -0.0 parameter are orphaned (dev caches only).
- Task 11: Ruling (perf, measured): 441-tile DiagramModel.build was 11.7 s (85 % render.splat recomputing identical weights per tile), rebuilt every 500 ms during a run. render._weights now caches (index, weight) per (net, n, sigma, pixels), ≤4 entries ~12 MB each; diagram_painter caches rendered tiles (_TILES, ≤1024 ~80 kB each) and T=0 segments. Cold build 2.45 s, warm 0.16 s. Tests: test_splat_matches_a_full_gaussian_sum (pins behaviour, passes before and after), test_tiles_of_one_diagram_share_their_splat_weights and test_a_rebuild_renders_only_tiles_it_has_not_seen (both RED→GREEN) — cost if wrong: ~100 MB extra RAM at most; a display change still takes ~2.5 s on 441 tiles (not "instant").
- Task 12: Ruling: window fixture gives each test its own PHASETILES_APP_DATA (result cache) — all windows shared one session cache, so "not computed yet" assertions depended on test order (test_run_controller computes the same J1=±1 tile) — cost: none.
- Task 12: Ruling: legend uses rich-text colour swatches (the brief's optional follow-up) instead of hex strings; info label is PlainText — cost: none.
- Task 13: Ruling: PreferencesDialog.apply refuses (returns False, shows a sentence) a path that is not a file — otherwise a typo leaves the app with no nets — cost: none.
- Task 13: Ruling: added test_a_missing_rcsr_file_at_startup_falls_back_and_says_so for the brief's "missing file at startup" requirement (brief had no test for it) — cost: none.
- Task 14: Ruling: tools/make_sample.py wraps its body in main() under `if __name__ == "__main__"` — the plan's top-level script crashed under spawn (BrokenProcessPool: workers re-ran the module) — cost: none.
- Task 14: Ruling: run_selftest calls application.app() first — without a QApplication, QPainter on a QImage aborted the test process; main() already made one, so the CLI path is unchanged — cost: none.
- Task 14: Ruling: phase-tiles.iss has no LicenseFile — the repo has no LICENSE file (pyproject says MIT); adding one is the user's call — cost: installer shows no licence page.
- Task 14: Ruling: .DS_Store added to .gitignore so `git add -A` (plan's commit step) does not commit Finder metadata — cost: none.
- Task 14: Ruling: icons drawn by tools/make_icon.py (plan named it in prose, not in Files) — .ico at 256 px — cost: none.
- Task 15: Ruling: Windows selftest path passed quoted (`"$PWDundle-selftest.png`") — Start-Process joins ArgumentList unquoted, and a runner path with a space would split — cost: none.
- Post-plan (user request 2026-10-12, branch feat/gui-layout 70f7a4c): window fits screen, scrolling foldable docks, docks not closable, spins+domains together, legend marks selected phase, selftest removes scratch dir. Ruling: "all windows not closable" read as the two docks — the main window must still close to quit — cost if wrong: one setFeatures line.
- Final: Ruling: test_an_invalid_range_disables_run_and_says_why now uses a reversed range — step 0 can no longer be typed — cost: none.

## Deferred minors (and what has since been fixed)

- Task 12: minor (deferred): phase label names the star by its canonical q (e.g. "q = (0, 1/2)") while the single domain shown may be the (1/2, 0) member — correct but can read as a contradiction.
- Task 13: minor (deferred): a user RCSR file that redefines a shipped net name (e.g. a different "sql") shares cache keys with the shipped net — results/renders keyed by name, not geometry.
- Final: fixed before the public release: validate() checks the tile cap before ax.values(), and a NaN/inf axis number is an error.
- Final: fixed before the public release: each pool worker gets the stop Event, so Stop interrupts running tiles.
- Final: minor (deferred): MAX_TILES caps count only, no time estimate; 5000-tile rebuild every 500 ms during a run.
- Final: fixed before the public release: Save and Export Image report an OSError in the status bar.
- Final: minor (deferred): fallback "T = 0 lines unavailable for this net." gives no reason.
- Final: minor (deferred): user RCSR file redefining a shipped net name shares cache keys (repeat of Task 13 minor); Task 12 phase-label wording.
