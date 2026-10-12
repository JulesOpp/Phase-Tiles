from phasetiles.spec import Axis, MCSettings
from phasetilesapp.run_controller import RunController


def _tiny(doc):
    doc.set_spec(doc.spec.replace(
        x=Axis("J1", -1, 1, 2.0), y=Axis("J2", 0, 0, 1.0),
        mc=MCSettings(n=12, anneal=100, equil=100, snaps=2)), "tiny")


def test_a_run_fills_the_tiles_and_reports(qtbot, window):
    w = window()
    _tiny(w.doc)
    rc = RunController(w.doc, workers=1)
    with qtbot.waitSignal(rc.finished, timeout=60000) as sig:
        rc.start()
    assert sig.args == [2, False]
    assert not rc.is_running()


def test_stop_ends_the_run_and_says_so(qtbot, window):
    w = window()
    w.doc.set_spec(w.doc.spec.replace(
        x=Axis("J1", -1, 1, 0.5), y=Axis("J2", -1, 1, 0.5),
        mc=MCSettings(n=12, anneal=2000, equil=2000, snaps=2)), "big")
    rc = RunController(w.doc, workers=1)
    with qtbot.waitSignal(rc.finished, timeout=60000) as sig:
        rc.start()
        rc.stop()
    assert sig.args[1] is True


def test_run_action_greys_out_while_running(qtbot, window):
    w = window()
    _tiny(w.doc)
    w.settings.workers = 1
    w.act_run.trigger()
    assert not w.act_run.isEnabled() and w.act_stop.isEnabled()
    qtbot.waitUntil(lambda: w.act_run.isEnabled(), timeout=60000)


def test_closing_during_a_run_stops_it_first(qtbot, window):
    w = window()
    w.doc.set_spec(w.doc.spec.replace(
        x=Axis("J1", -1, 1, 0.5), y=Axis("J2", -1, 1, 0.5),
        mc=MCSettings(n=12, anneal=2000, equil=2000, snaps=2)), "big")
    w.settings.workers = 1
    w.act_run.trigger()
    w.doc.stack.mark_clean()
    assert w.close()
    assert not w.runner.is_running()
