from phasetiles import nets
from phasetilesapp.setup_dock import SetupDock


def _dock(window):
    w = window()
    return w, w.findChild(SetupDock)


def test_family_lists_common_then_plane_groups(window):
    _, d = _dock(window)
    items = [d.family.itemText(i) for i in range(d.family.count())]
    assert items[0] == "Common"
    assert set(items[1:]) <= set(nets.PLANE_GROUPS)


def test_choosing_kagome_is_one_undo_step(window):
    w, d = _dock(window)
    d.net.setCurrentIndex(d.net.findData("kgm"))
    assert w.doc.spec.net == "kgm"
    w.doc.undo()
    assert w.doc.spec.net == "sql"
    assert d.net.currentData() == "sql"


def test_picking_a_plane_group_lists_its_nets(window):
    _, d = _dock(window)
    d.family.setCurrentText("p4mm")
    names = [d.net.itemData(i) for i in range(d.net.count())]
    assert "sql" in names and all(
        nets.list_2d()[k][0] == "p4mm" for k in names)


def test_ticking_the_field_term_adds_h_and_updates_formula(window):
    w, d = _dock(window)
    d.ham.rows["H"].check.setChecked(True)
    assert "H" in w.doc.spec.hamiltonian.symbols()
    assert "H Σ sᵢ" in d.ham.formula.text()


def test_shell_info_follows_the_net(window):
    w, d = _dock(window)
    assert "4 neighbours" in d.ham.rows["J2"].info.text()
    d.net.setCurrentIndex(d.net.findData("hxl"))
    assert "6 neighbours" in d.ham.rows["J2"].info.text()


def test_unticking_a_term_on_an_axis_is_refused_with_a_reason(window):
    w, d = _dock(window)
    d.ham.rows["J2"].check.setChecked(False)
    assert d.ham.rows["J2"].check.isChecked()
    assert "Y axis" in d.messages.text()


def test_an_invalid_range_disables_run_and_says_why(window):
    w, d = _dock(window)
    d.x_step.setValue(0.0)
    d.x_step.editingFinished.emit()
    assert not w.act_run.isEnabled()
    assert "step must be > 0" in d.messages.text()


def test_typing_a_value_is_one_undo_step(window):
    w, d = _dock(window)
    before = len(w.doc.stack._cmds)
    d.x_start.setValue(-0.5)
    d.x_start.editingFinished.emit()
    assert len(w.doc.stack._cmds) == before + 1
