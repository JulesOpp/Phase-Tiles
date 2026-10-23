# -*- mode: python ; coding: utf-8 -*-
"""Phase Tiles for macOS: pyinstaller --noconfirm packaging/macos.spec
Onedir in a .app.  Two architectures (macos-14 arm64, macos-15-intel
x86_64), never universal2 -- the wheels are per-arch."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(SPECPATH)))
import bundle  # noqa: E402

a = Analysis([str(bundle.ROOT / "phasetilesapp" / "main.py")],
             pathex=[str(bundle.ROOT)],
             datas=bundle.project_datas() + bundle.licence_datas(),
             hiddenimports=bundle.HIDDEN_IMPORTS,
             excludes=bundle.EXCLUDES)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=bundle.NAME,
          console=False, icon=str(bundle.ICONS / "phase-tiles.icns"))
coll = COLLECT(exe, a.binaries, a.datas, name=bundle.NAME)
app = BUNDLE(coll, name=bundle.NAME + ".app",
             icon=str(bundle.ICONS / "phase-tiles.icns"),
             bundle_identifier="org.phasetiles.app",
             info_plist={"CFBundleShortVersionString": bundle.version(),
                         "NSHighResolutionCapable": True,
                         "NSHumanReadableCopyright": bundle.COPYRIGHT,
                         "LSMinimumSystemVersion": bundle.MACOS_MIN,
                         "CFBundleDocumentTypes": [{
                             "CFBundleTypeName": "Phase Tiles diagram",
                             "CFBundleTypeExtensions": ["phtiles"],
                             "CFBundleTypeRole": "Editor"}]})
