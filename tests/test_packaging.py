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


def test_the_bundle_carries_every_licence_its_contents_need():
    datas = bundle.licence_datas()
    for src, _ in datas:
        assert pathlib.Path(src).is_file(), src
    names = {(pathlib.Path(s).name, d.split("/")[1] if "/" in d else "")
             for s, d in datas}
    assert ("LICENSE", "") in names
    assert ("THIRD-PARTY-NOTICES.txt", "") in names
    assert ("LGPL-3.0.txt", "qt") in names
    for pkg in bundle.NOTICE_PACKAGES:
        assert any(d.startswith(f"licenses/{pkg}") for _, d in datas), pkg


def test_the_mac_app_states_the_macos_it_is_checked_against():
    # LSMinimumSystemVersion and check_macos_min.py read one constant,
    # so the Finder's "needs a newer macOS" and CI's check agree
    spec_text = (ROOT / "packaging" / "macos.spec").read_text()
    assert '"LSMinimumSystemVersion": bundle.MACOS_MIN' in spec_text
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "packaging/macos_wheels.py" in ci
    assert "packaging/check_macos_min.py" in ci
