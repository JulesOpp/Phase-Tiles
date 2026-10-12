from phasetiles import project, runner
from phasetiles.spec import Axis, MCSettings, default_spec
from phasetiles.store import ResultStore


def test_a_saved_project_reopens_with_its_tiles(tmp_path):
    s = default_spec().replace(
        x=Axis("J1", -1, 1, 2.0), y=Axis("J2", 0, 0, 1.0),
        mc=MCSettings(n=12, anneal=50, equil=50, snaps=1))
    a = ResultStore(tmp_path / "a")
    runner.run_tiles(s, a, 1)
    project.save_project(tmp_path / "x.phtiles", s, a)
    b = ResultStore(tmp_path / "b")
    t = project.load_project(tmp_path / "x.phtiles", b)
    assert t == s and runner.jobs_for(t, b) == []


def test_a_project_cannot_write_outside_the_cache(tmp_path):
    import zipfile
    f = tmp_path / "evil.phtiles"
    with zipfile.ZipFile(f, "w") as z:
        z.writestr("spec.json", default_spec().to_json())
        z.writestr("tiles/../../escaped.npz", b"x")
        z.writestr("tiles/k/../../../escaped2.npz", b"x")
    st = ResultStore(tmp_path / "cache" / "inner")
    project.load_project(f, st)
    assert not list(tmp_path.rglob("escaped*.npz"))
