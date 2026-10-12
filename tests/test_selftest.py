import pytest

from phasetilesapp.selftest import run_selftest


@pytest.mark.slow
def test_selftest_writes_an_image_and_passes(tmp_path, capsys):
    out = tmp_path / "self.png"
    assert run_selftest(str(out)) == 0
    assert out.stat().st_size > 10000
    assert "selftest passed" in capsys.readouterr().out


@pytest.mark.slow
def test_selftest_removes_its_scratch_folder(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    out = tmp_path / "keep.png"
    assert run_selftest(str(out)) == 0
    assert [p.name for p in tmp_path.iterdir()] == ["keep.png"]
