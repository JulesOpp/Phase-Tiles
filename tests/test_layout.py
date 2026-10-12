"""The window must fit a laptop screen: the setup dock scrolls, its
sections fold, and no dock can be closed (a closed dock had no menu
entry to bring it back)."""
from PySide6.QtWidgets import QDockWidget, QScrollArea

from phasetilesapp.collapsible import Section
from phasetilesapp.domains_panel import DomainsPanel
from phasetilesapp.setup_dock import SetupDock


def test_no_dock_can_be_closed(window):
    w = window()
    docks = w.findChildren(QDockWidget)
    assert len(docks) == 2
    for d in docks:
        assert not (d.features()
                    & QDockWidget.DockWidgetFeature.DockWidgetClosable)


def test_both_docks_scroll(window):
    w = window()
    for cls in (SetupDock, DomainsPanel):
        assert isinstance(w.findChild(cls).widget(), QScrollArea)


def test_setup_sections_fold_and_unfold(window):
    w = window()
    secs = w.findChild(SetupDock).findChildren(Section)
    assert [s.title() for s in secs] == [
        "Topology", "Hamiltonian (J > 0 ferro)", "Varied parameters",
        "Monte Carlo"]
    s = secs[0]
    s.toggle.click()
    assert s.body.isHidden()
    s.toggle.click()
    assert not s.body.isHidden()


def test_the_window_fits_the_screen(window):
    w = window()
    avail = w.screen().availableGeometry()
    assert w.height() <= avail.height()
    assert w.minimumSizeHint().height() <= avail.height()
    # and a 1280 x 720 laptop, whatever the test screen is
    assert w.minimumSizeHint().width() <= 1280
    assert w.minimumSizeHint().height() <= 720


def test_the_widest_setup_row_is_not_cut_off(window):
    w = window()
    d = w.findChild(SetupDock)
    area = d.widget()
    assert area.minimumWidth() >= (
        area.widget().minimumSizeHint().width()
        + area.verticalScrollBar().sizeHint().width())

