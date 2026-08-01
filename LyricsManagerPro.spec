# -*- mode: python ; coding: utf-8 -*-
"""Konfiguracja PyInstallera dla Lyrics Manager Pro.

Budowanie:  pyinstaller --noconfirm LyricsManagerPro.spec
Wynik:      dist/LyricsManagerPro.exe  (jeden plik, bez okna konsoli)
"""

import customtkinter
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

CTK_PATH = Path(customtkinter.__file__).parent

# spylls to silnik sprawdzania pisowni (Hunspell w czystym Pythonie).
# Jego wlasne przykladowe slowniki (en/ru/sv, ~5 MB) sa niepotrzebne -
# aplikacja wczytuje slowniki z katalogu uzytkownika, wiec ich nie pakujemy.
SPYLLS_MODULES = collect_submodules("spylls")

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=[
        (str(CTK_PATH), "customtkinter"),   # motywy i zasoby CustomTkinter
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
    # przykladowe slowniki spylls pomijamy - patrz komentarz wyzej
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LyricsManagerPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,              # aplikacja okienkowa, bez konsoli
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/app.ico",
)
