def test_menus_hold_the_promised_entries(window):
    w = window()
    titles = [a.text().replace("&", "") for a in w.menuBar().actions()]
    assert titles[:5] == ["File", "Edit", "Run", "View", "Help"]
    file_items = [a.text().replace("&", "")
                  for a in w.menu_file.actions() if a.text()]
    assert "Export Image…" in file_items


def test_undo_action_follows_the_document(window):
    w = window()
    assert not w.act_undo.isEnabled()
    w.doc.set_spec(w.doc.spec.replace(net="kgm"), "Change net")
    assert w.act_undo.isEnabled()
    assert "Change net" in w.act_undo.text()


def test_tile_centre_actions_are_exclusive_and_undoable(window):
    w = window()
    w.act_centre_half.trigger()
    assert w.doc.spec.display.centre == "half"
    assert w.act_centre_half.isChecked()
    w.act_undo.trigger()
    assert w.act_centre_gamma.isChecked()
