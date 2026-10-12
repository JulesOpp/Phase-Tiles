import numpy as np
import pytest

from phasetiles import nets


def test_every_shipped_2d_net_has_the_coordination_rcsr_lists():
    names = nets.list_2d()
    assert len(names) == 199
    for name in names:
        n = nets.Net(name, nshell=1)
        assert (n.degree == n.coord).all(), name


@pytest.mark.parametrize("name,nsub,z", [
    ("sql", 1, [[4], [4], [4]]),
    ("hxl", 1, [[6], [6], [6]]),
    ("hcb", 2, [[3, 3], [6, 6], [3, 3]]),
    ("kgm", 3, [[4, 4, 4], [4, 4, 4], [6, 6, 6]]),
])
def test_common_nets_have_the_textbook_shells(name, nsub, z):
    n = nets.Net(name, nshell=3)
    assert n.nsub == nsub
    assert n.shell_counts()[:3] == z


def test_square_shell_distances_are_1_root2_2():
    n = nets.Net("sql", nshell=3)
    assert np.allclose(n.shell_dist[:3], [1, 2 ** .5, 2], atol=1e-3)


def test_common_and_plane_group_families_cover_every_net():
    fam = {g for g, _ in nets.list_2d().values()}
    assert fam <= set(nets.PLANE_GROUPS)
    assert [k for _, k in nets.COMMON] == ["sql", "hxl", "hcb", "kgm"]


def test_a_user_rcsr_file_replaces_the_shipped_one(tmp_path):
    f = tmp_path / "mini.cgd"
    f.write_text("CRYSTAL\n  NAME sql\n  GROUP p4mm\n"
                 "  CELL 1.0 1.0 90.0\n  NODE 1 4 0.0 0.0\n"
                 "  EDGE 0.0 0.0 0.0 1.0\nEND\n")
    try:
        nets.set_source(str(f))
        assert list(nets.list_2d()) == ["sql"]
    finally:
        nets.set_source(None)
    assert len(nets.list_2d()) == 199
