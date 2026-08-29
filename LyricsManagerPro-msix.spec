# -*- mode: python ; coding: utf-8 -*-
"""Wariant budowania dla pakietu MSIX (Microsoft Store).

Rozni sie od LyricsManagerPro.spec jedna, ale istotna rzecza: buduje katalog,
a nie pojedynczy plik. W MSIX pliki i tak leza wewnatrz pakietu, a wersja
jednoplikowa rozpakowywalaby sie do %TEMP% przy kazdym uruchomieniu - wolniej
i bez sensu.

Budowanie:  pyinstaller --noconfirm LyricsManagerPro-msix.spec
Wynik:      dist/LyricsManagerPro-msix/  (LyricsManagerPro.exe + _internal)
"""

import customtkinter
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

CTK_PATH = Path(customtkinter.__file__).parent
SPYLLS_MODULES = collect_submodules("spylls")

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=[
        (str(CTK_PATH), "customtkinter"),
        ("assets/app.ico", "assets"),
    ],
    hiddenimports=[
        *SPYLLS_MODULES,
        "customtkinter",
        "requests",
        "sqlite3",
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.font",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "numpy", "pandas", "scipy", "PIL", "pytest",
        "IPython", "notebook", "setuptools", "pip",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # reszta trafia do COLLECT
    name="LyricsManagerPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/app.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LyricsManagerPro-msix",
)
