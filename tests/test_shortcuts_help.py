"""Testy skrotow klawiszowych i instrukcji obslugi.

Sprawdza spojnosc tabeli skrotow, kompletnosc tlumaczen, faktyczne przypisanie
w oknie oraz to, ze skroty przechwytuja wbudowane skroty widgetu tekstowego Tk.
Uruchomienie: python tests\\test_shortcuts_help.py
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyrics_manager.help_content import CONTENT, SECTION_KEYS
from lyrics_manager.i18n import LANGUAGES, get_ui_language, set_ui_language, tr
from lyrics_manager.shortcuts import GROUPS, SHORTCUTS, bindable, by_group
from lyrics_manager.ui import theme
from lyrics_manager.ui.app import LyricsManagerApp
from lyrics_manager.ui.help_window import HelpWindow

FAILURES: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f"{label}: oczekiwano {expected!r}, jest {actual!r}")


def check_true(label: str, condition: bool) -> None:
    if not condition:
        FAILURES.append(f"{label}: warunek nie zostal spelniony")


# --- tabela skrotow -------------------------------------------------------

actions = [s.action for s in SHORTCUTS]
check("brak zdublowanych akcji", len(actions), len(set(actions)))

labels = [s.label for s in SHORTCUTS]
check("brak zdublowanych etykiet", len(labels), len(set(labels)))

all_sequences = [seq for s in SHORTCUTS for seq in s.sequences]
check("brak zdublowanych sekwencji", len(all_sequences), len(set(all_sequences)))

check_true("kazdy skrot ma znana grupe", all(s.group in GROUPS for s in SHORTCUTS))
check_true("skroty nienatywne maja sekwencje",
           all(s.sequences for s in SHORTCUTS if not s.native))
check_true("skroty natywne nie maja sekwencji",
           all(not s.sequences for s in SHORTCUTS if s.native))
check_true("kazda grupa ma jakis skrot", all(by_group(g) for g in GROUPS))

# --- tlumaczenia ----------------------------------------------------------

for lang in LANGUAGES:
    set_ui_language(lang)
    for shortcut in SHORTCUTS:
        key = f"key.{shortcut.action}"
        check_true(f"opis skrotu {shortcut.action} [{lang}]", tr(key) != key)
    for group in GROUPS:
        key = f"key.group.{group}"
        check_true(f"nazwa grupy {group} [{lang}]", tr(key) != key)
    for section in SECTION_KEYS:
        key = f"help.sec.{section}"
        check_true(f"tytul sekcji {section} [{lang}]", tr(key) != key)

# --- tresc instrukcji -----------------------------------------------------

for section in SECTION_KEYS:
    if section == "shortcuts":       # generowana z tabeli skrotow
        continue
    for lang in LANGUAGES:
        body = CONTENT.get(section, {}).get(lang, "")
        check_true(f"tresc sekcji {section} [{lang}] istnieje", bool(body.strip()))
        check_true(f"tresc sekcji {section} [{lang}] ma naglowek",
                   body.strip().startswith("# "))
        check_true(f"tresc sekcji {section} [{lang}] ma sensowna dlugosc",
                   len(body) > 400)

# obie wersje jezykowe powinny miec zblizona objetosc
for section in SECTION_KEYS:
    if section == "shortcuts":
        continue
    pl = len(CONTENT[section]["pl"])
    en = len(CONTENT[section]["en"])
    ratio = min(pl, en) / max(pl, en)
    check_true(f"sekcja {section}: PL i EN podobnej dlugosci ({pl}/{en})", ratio > 0.6)

# --- okno aplikacji -------------------------------------------------------

set_ui_language("pl")
app = LyricsManagerApp()
app.withdraw()
app.update()

# kazdy skrot ma przypisana akcje
handlers = app._shortcut_actions()
for shortcut in bindable():
    check_true(f"akcja dla {shortcut.action}", shortcut.action in handlers)

# Sekwencje sa faktycznie zwiazane z oknem i z edytorem.
# Tk normalizuje zapis (<Control-n> staje sie <Control-Key-n>), wiec zamiast
# porownywac napisy pytamy Tk o skrypt przypisany do danej sekwencji.
for shortcut in bindable():
    for sequence in shortcut.sequences:
        check_true(f"okno zna {sequence}", bool(app.bind(sequence)))
        if shortcut.editor_break:
            check_true(f"edytor przechwytuje {sequence}",
                       bool(app.editor.text.bind(sequence)))

# --- dzialanie skrotow ----------------------------------------------------

app.set_text("Wers pierwszy\nWers drugi\n")
app.update()

# Skroty kolidujace z wbudowanymi skrotami widgetu Text nie moga zmieniac
# tekstu. Probujemy tylko tych bez efektow ubocznych - Ctrl+O otwiera okno
# wyboru pliku, wiec w tescie automatycznym go nie generujemy.
#   Ctrl+K w czystym Tk kasuje tekst do konca wersu
#   Ctrl+T w czystym Tk zamienia miejscami dwa znaki
for sequence, name in (("<Control-k>", "Ctrl+K"), ("<Control-t>", "Ctrl+T")):
    app.editor.text.mark_set("insert", "1.5")
    before = app.get_text()
    app.editor.text.event_generate(sequence)
    app.update()
    check(f"{name} nie zmienia tekstu", app.get_text(), before)

# przelaczanie zakladek
app.editor.text.event_generate("<Alt-Key-2>")
app.update()
check("Alt+2 otwiera Rymy", app.tabs.get(), "rhymes")
app.editor.text.event_generate("<Alt-Key-5>")
app.update()
check("Alt+5 otwiera Pisownie", app.tabs.get(), "spelling")

# rozmiar czcionki
start_size = int(app.settings.get("editor_font_size", 14))
app._change_font_size(1)
check("powiekszenie czcionki", int(app.settings.get("editor_font_size")), start_size + 1)
app._change_font_size(0)
check("reset czcionki", int(app.settings.get("editor_font_size")), 14)

# Przelaczniki jezyka i motywu. Sprawdzamy wzglednie, bo program wczytuje
# zapisany stan z ustawien i nie zawsze startuje po polsku.
before_text_lang = app.text_language()
app._toggle_text_language()
check_true("przelacznik jezyka tekstu zmienia jezyk",
           app.text_language() != before_text_lang)
app._toggle_text_language()
check("powrot jezyka tekstu", app.text_language(), before_text_lang)

before_ui_lang = get_ui_language()
app._toggle_ui_language()
check_true("przelacznik jezyka UI zmienia jezyk", get_ui_language() != before_ui_lang)
app._toggle_ui_language()
check("powrot jezyka UI", get_ui_language(), before_ui_lang)

before_dark = theme.is_dark()
app._toggle_theme()
check_true("przelacznik motywu zmienia motyw", theme.is_dark() != before_dark)
app._toggle_theme()
check("powrot motywu", theme.is_dark(), before_dark)

# wstawianie sekcji skrotem
before = app.get_text()
app._insert_section(tr("sec.chorus"))
app.update()
check_true("skrot wstawia refren", "[Chorus]" in app.get_text())
app.set_text(before)

# --- okno pomocy ----------------------------------------------------------

app.open_help()
app.update()
help_window = app._help_window
check_true("okno pomocy powstalo", isinstance(help_window, HelpWindow))

if help_window is not None:
    for section in SECTION_KEYS:
        try:
            help_window.show(section)
            app.update()
        except Exception as exc:  # noqa: BLE001
            FAILURES.append(f"sekcja pomocy {section}: {type(exc).__name__}: {exc}")
    help_window.show("shortcuts")
    app.update()
    rendered = help_window.text.get("1.0", "end-1c")
    check_true("sekcja skrotow ma tresc", len(rendered) > 200)
    check_true("sekcja skrotow wymienia Ctrl+S", "Ctrl+S" in rendered)
    check_true("sekcja skrotow wymienia F7", "F7" in rendered)
    check_true("sekcja skrotow ma opisy po polsku",
               "Sprawdź pisownię" in rendered or "Check spelling" in rendered)

    # pogrubienia musza zostac pogrubione: znacznik akapitu obejmuje caly
    # wiersz i bez podniesienia priorytetu nadpisalby czcionke fragmentu
    help_window.show("start")
    app.update()
    bold_ranges = help_window.text.tag_ranges("strong")
    check_true("instrukcja zawiera pogrubienia", len(bold_ranges) >= 2)
    if bold_ranges:
        used = help_window.text.tag_names(bold_ranges[0])
        winner = None
        for name in reversed(help_window.text.tag_names()):
            if name in used and help_window.text.tag_cget(name, "font"):
                winner = name
                break
        check("pogrubienie ma najwyzszy priorytet", winner, "strong")

    # eksport instrukcji do pliku
    for lang in LANGUAGES:
        set_ui_language(lang)
        help_window.refresh_labels()
        app.update()
        markdown = help_window.as_markdown()
        check_true(f"eksport [{lang}] ma naglowki", markdown.count("\n## ") >= 10)
        check_true(f"eksport [{lang}] ma tabele skrotow", "| `Ctrl+S` |" in markdown)
        check_true(f"eksport [{lang}] ma sensowna dlugosc", len(markdown) > 8000)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / f"instrukcja_{lang}.md"
            target.write_text(markdown, encoding="utf-8")
            check_true(f"plik [{lang}] zapisany", target.stat().st_size > 8000)

    # ponowne otwarcie nie tworzy drugiego okna
    existing = app._help_window
    app.open_help()
    app.update()
    check("open_help nie duplikuje okna", app._help_window, existing)

    help_window.destroy()
    app.update()

set_ui_language("pl")
app._dirty = False
try:
    for snapshot in app.history.list(app.song_key()):
        app.history.delete(snapshot.id)
except Exception:  # noqa: BLE001
    pass
app.destroy()

# --- wynik ----------------------------------------------------------------

if FAILURES:
    print(f"NIEPOWODZENIA ({len(FAILURES)}):")
    for failure in FAILURES:
        print("  -", failure)
    raise SystemExit(1)

print("Wszystkie testy skrotow i instrukcji przeszly.")
