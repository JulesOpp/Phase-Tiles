"""Entry point.

freeze_support() must be the first thing that runs: in a frozen
build each spawned MC worker re-executes this file, and without it
every worker would open a window (CLAUDE.md invariant).
"""
import multiprocessing
import sys


def main(argv=None):
    multiprocessing.freeze_support()
    argv = sys.argv[1:] if argv is None else argv
    from phasetilesapp.application import app
    a = app()
    if argv[:1] == ["--selftest"]:
        from phasetilesapp.selftest import run_selftest
        return run_selftest(argv[1] if len(argv) > 1 else None)
    if argv[:1] == ["--render"]:
        from phasetilesapp.export import render_spec
        return render_spec(argv[1], argv[2])
    from phasetilesapp.mainwindow import MainWindow
    w = MainWindow()
    w.show()
    return a.exec()


if __name__ == "__main__":
    sys.exit(main())
