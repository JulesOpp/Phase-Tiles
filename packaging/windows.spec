# -*- mode: python ; coding: utf-8 -*-
"""Phase Tiles for Windows: pyinstaller --noconfirm packaging\\windows.spec
Onedir (Inno Setup installs a directory).  Contents come from
bundle.py, shared with macos.spec; what is here is the .ico and the
version resource, generated per build because it carries the
setuptools-scm version."""
import sys
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

sys.path.insert(0, str(Path(SPECPATH)))
import bundle  # noqa: E402

v = bundle.windows_version()
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=v, prodvers=v),
    kids=[StringFileInfo([StringTable("040904B0", [
              StringStruct("CompanyName", "Phase Tiles"),
              StringStruct("FileDescription",
                           "Tiled Ising phase diagrams on 2D nets"),
              StringStruct("FileVersion", bundle.version()),
              StringStruct("LegalCopyright", bundle.COPYRIGHT),
              StringStruct("ProductName", "Phase Tiles"),
              StringStruct("ProductVersion", bundle.version())])]),
          VarFileInfo([VarStruct("Translation", [1033, 1200])])])

a = Analysis([str(bundle.ROOT / "phasetilesapp" / "main.py")],
             pathex=[str(bundle.ROOT)],
             datas=bundle.project_datas() + bundle.licence_datas(),
             hiddenimports=bundle.HIDDEN_IMPORTS,
             excludes=bundle.EXCLUDES)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=bundle.NAME,
          console=False, icon=str(bundle.ICONS / "phase-tiles.ico"),
          version=version_info)
coll = COLLECT(exe, a.binaries, a.datas, name=bundle.NAME)
