"""Punkt wejscia aplikacji Lyrics Manager Pro."""

from __future__ import annotations

import sys
from pathlib import Path


def _enable_dpi_awareness() -> None:
    """Ostre czcionki na ekranach HiDPI w Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def _resource_path(relative: str) -> Path:
    """Sciezka do zasobu - dziala tez w pliku .exe spakowanym PyInstallerem."""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parent.parent
    return root / relative


def self_test() -> str:
    """Krotki raport o stanie srodowiska.

    Aplikacja jest oknem bez konsoli, wiec przy `--selftest` raport trafia do
    pliku. Przydaje sie, gdy trzeba sprawdzic, czy w spakowanym .exe sa
    wszystkie zaleznosci i ktore slowniki widzi program.
    """
    from . import APP_NAME, APP_VERSION
    from .config import data_dir

    lines = [f"{APP_NAME} {APP_VERSION}", f"Python: {sys.version.split()[0]}",
             f"Frozen: {getattr(sys, 'frozen', False)}",
             f"Katalog danych: {data_dir()}"]

    for module in ("customtkinter", "requests", "spylls", "sqlite3", "tkinter"):
        try:
            __import__(module)
            lines.append(f"[OK]   {module}")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"[BRAK] {module}: {exc}")

    try:
        from .spelling import SpellChecker, dictionaries_dir, installed_codes
        codes = installed_codes()
        lines.append(f"Silnik pisowni: {'dostepny' if SpellChecker.engine_available() else 'BRAK'}")
        lines.append(f"Katalog slownikow: {dictionaries_dir()}")
        lines.append(f"Slowniki: {', '.join(codes) if codes else '(brak)'}")

        if codes:
            checker = SpellChecker()
            code = codes[0]
            checker.load(code)
            probe = "qwertyuiopasdfgh"
            lines.append(
                f"Test slownika {code}: "
                f"blad wykryty = {not checker.check_word(probe, code, code[:2])}"
            )
    except Exception as exc:  # noqa: BLE001
        lines.append(f"[BLAD] pisownia: {type(exc).__name__}: {exc}")

    try:
        from .help_content import CONTENT, SECTION_KEYS
        from .shortcuts import SHORTCUTS, bindable
        filled = sum(
            1 for key in SECTION_KEYS
            if key == "shortcuts" or all(CONTENT.get(key, {}).get(lang, "").strip()
                                         for lang in ("pl", "en"))
        )
        lines.append(f"Instrukcja: {filled}/{len(SECTION_KEYS)} sekcji w PL i EN")
        lines.append(f"Skroty: {len(SHORTCUTS)} pozycji, {len(bindable())} przypisanych")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"[BLAD] instrukcja/skroty: {type(exc).__name__}: {exc}")

    return "\n".join(lines)


def main() -> int:
    _enable_dpi_awareness()

    if "--selftest" in sys.argv:
        report = self_test()
        index = sys.argv.index("--selftest")
        target = sys.argv[index + 1] if len(sys.argv) > index + 1 else None
        if target:
            Path(target).write_text(report, encoding="utf-8")
        else:
            print(report)
        return 0

    from .ui.app import LyricsManagerApp

    app = LyricsManagerApp()

    # plik podany w wierszu polecen albo upuszczony na ikone programu
    for argument in sys.argv[1:]:
        if argument.startswith("-"):
            continue
        candidate = Path(argument)
        if candidate.is_file():
            app.open_path(str(candidate))
            break

    icon = _resource_path("assets/app.ico")
    if icon.exists():
        try:
            app.iconbitmap(str(icon))
        except Exception:
            pass

    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
