"""bundle.py must name every data file the app reads: a file read
but not bundled works on a checkout and fails in every installer."""
import importlib.util
import pathlib

from phasetiles import resources

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "bundle", ROOT / "packaging" / "bundle.py")
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


def test_bundle_names_every_required_data_file():
    dests = {pathlib.PurePosixPath(d) / pathlib.Path(s).name
             for s, d in bundle.project_datas()}
    for name in resources.REQUIRED:
        want = pathlib.PurePosixPath("phasetiles/data") / name
        assert want in dests, name


def test_every_required_file_exists_in_the_checkout():
    for name in resources.REQUIRED:
        with resources.path(name) as p:
            assert p.exists(), name


def test_nothing_in_data_is_unlisted():
    data = ROOT / "phasetiles" / "data"
    shipped = {str(p.relative_to(data)).replace("\\", "/")
               for p in data.rglob("*") if p.is_file()
               and p.suffix != ".md"}
    assert shipped == set(resources.REQUIRED)


def test_bundle_never_collects_matplotlib_or_tests():
    assert {"matplotlib", "tkinter", "pytest"} <= set(bundle.EXCLUDES)
