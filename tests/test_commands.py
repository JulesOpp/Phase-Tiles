from phasetiles.commands import CommandStack, SetSpec
from phasetiles.spec import default_spec


def test_undo_and_redo_restore_specs_and_cleanliness():
    a = default_spec()
    b = a.replace(net="kgm")
    st = CommandStack(a)
    assert st.is_clean and not st.can_undo
    st.push(SetSpec(a, b, "Change net"))
    assert st.current == b and not st.is_clean
    assert st.undo_text == "Change net"
    st.undo()
    assert st.current == a and st.is_clean
    st.redo()
    assert st.current == b


def test_pushing_after_undo_discards_the_redo_branch():
    a = default_spec()
    st = CommandStack(a)
    st.push(SetSpec(a, a.replace(net="kgm"), "x"))
    st.undo()
    st.push(SetSpec(a, a.replace(net="hcb"), "y"))
    assert not st.can_redo and st.current.net == "hcb"


def test_saving_marks_clean_at_that_point_only():
    a = default_spec()
    st = CommandStack(a)
    st.push(SetSpec(a, a.replace(net="kgm"), "x"))
    st.mark_clean()
    st.undo()
    assert not st.is_clean
