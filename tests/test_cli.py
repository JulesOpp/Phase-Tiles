from phasetiles import cli


def test_nets_lists_all_199(capsys):
    assert cli.main(["nets"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 199


def test_info_prints_shells(capsys):
    cli.main(["info", "--net", "kgm"])
    assert "J3" in capsys.readouterr().out


def test_an_invalid_range_exits_with_the_sentence(capsys):
    assert cli.main(["run", "--net", "sql", "--vary", "J1=1:-1:0.1",
                     "--vary", "J2=-1:1:0.1", "--fix", "T=0.5"]) == 2
    assert "above stop" in capsys.readouterr().err


def test_run_computes_tiles_into_the_cache(capsys):
    assert cli.main(["run", "--net", "sql", "--vary", "J1=-1:1:2",
                     "--vary", "J2=0:0:1", "--fix", "T=0.5", "--n",
                     "12", "--anneal", "50", "--equil", "50",
                     "--snaps", "1", "--workers", "1"]) == 0
    assert "2 tiles computed" in capsys.readouterr().out
