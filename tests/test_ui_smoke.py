"""Test dymny interfejsu: budowa okna, przelaczenie jezyka, motywu i zakladek.

Okno jest tworzone, przetwarzane i zamykane bez udzialu uzytkownika.
Uruchomienie: python tests\\test_ui_smoke.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyrics_manager.i18n import tr
from lyrics_manager.ui.app import LyricsManagerApp

SAMPLE = """[Zwrotka 1]
Wracam do domu nocna droga
Swiatla miasta gasna z tylu
Nie ma juz nic co mnie tu trzyma
Tylko cien na mokrym pylu

[Refren]
Biegne przez deszcz
Biegne przez deszcz
Nie zatrzyma mnie nic
"""

FAILURES: list[str] = []


def step(label: str, fn) -> None:
    try:
        fn()
        app.update()
        app.update_idletasks()
    except Exception as exc:  # noqa: BLE001
        FAILURES.append(f"{label}: {type(exc).__name__}: {exc}")


def _open_and_close_manager(app) -> None:
    """Buduje okno zarzadzania slownikami i od razu je zamyka."""
    app.panel_spelling.open_manager()
    app.update()
    for child in list(app.winfo_children()):
        if child.winfo_class() == "Toplevel":
            child.grab_release()
            child.destroy()
    app.update()


def _open_context_menu(app, word: str) -> None:
    """Buduje menu kontekstowe dla slowa, nie pokazujac go na ekranie."""
    import tkinter as tk

    posted: list[tk.Menu] = []
    original_popup = tk.Menu.tk_popup
    tk.Menu.tk_popup = lambda self, *a, **kw: posted.append(self)
    try:
        text = app.editor.text
        for line_no, line in enumerate(app.get_text().splitlines(), start=1):
            col = line.find(word)
            if col < 0:
                continue

            class FakeEvent:
                pass

            event = FakeEvent()
            bbox = text.bbox(f"{line_no}.{col}") or (0, 0, 1, 1)
            event.x, event.y = bbox[0] + 1, bbox[1] + 1
            event.x_root = event.y_root = 0
            app._on_editor_context(event)
            break
    finally:
        tk.Menu.tk_popup = original_popup
    for menu in posted:
        menu.destroy()


app = LyricsManagerApp()
app.withdraw()          # nie pokazuj okna podczas testu
app.update()

step("wpisanie tekstu", lambda: app.set_text(SAMPLE))
step("analiza", lambda: app._run_analysis())

step("zakladka rymy", lambda: app.tabs.select("rhymes"))
step("zakladka powtorzenia", lambda: app.tabs.select("repetitions"))
step("zakladka czytelnosc", lambda: app.tabs.select("readability"))
step("zakladka historia", lambda: app.tabs.select("history"))
step("zakladka eksport", lambda: app.tabs.select("export"))
step("zakladka AI", lambda: app.tabs.select("ai"))
step("zakladka pisownia", lambda: app.tabs.select("spelling"))
step("zakladka sylaby", lambda: app.tabs.select("syllables"))

# --- pisownia ---------------------------------------------------------
step("sprawdzenie pisowni", lambda: app.request_spellcheck(force=True))
# slownik wczytuje sie w watku (polski ~3,5 s), wiec czekamy na stan koncowy;
# "off" na starcie to stan poczatkowy, a nie wynik - nie przerywa czekania
if app.settings.get("spell_check_enabled", True):
    deadline = time.time() + 40
    while time.time() < deadline:
        app.update()
        if app._spell_state in ("ready", "missing", "no_engine"):
            break
        time.sleep(0.2)
print(f"  stan pisowni: {app._spell_state}, slownik: {app.spell_code()}")

if app._spell_state == "ready":
    step("wylaczenie pisowni", lambda: (
        app.panel_spelling.enabled_var.set(False),
        app.panel_spelling._toggle_enabled(),
    ))
    step("wlaczenie pisowni", lambda: (
        app.panel_spelling.enabled_var.set(True),
        app.panel_spelling._toggle_enabled(),
    ))
    step("odswiezenie listy slownikow",
         lambda: app.panel_spelling.refresh_dictionary_list())
    step("zamiana slowa w calym tekscie",
         lambda: app.editor.replace_word_everywhere("juz", "już"))
    step("dodanie slowa do slownika", lambda: app._add_to_dictionary("cien"))
    step("ignorowanie slowa", lambda: app._ignore_word("mokrym"))
    step("ponowne sprawdzenie", lambda: app.request_spellcheck(force=True))
    step("cofniecie wpisu w slowniku",
         lambda: app.spell.personal.remove("cien", app.text_language()))
    step("menu kontekstowe na bledzie", lambda: _open_context_menu(app, "juz"))
else:
    print("  (pominieto akcje pisowni - slownik niedostepny)")

# okno zarzadzania slownikami dziala niezaleznie od tego, czy slownik jest
step("okno slownikow", lambda: _open_and_close_manager(app))

step("jezyk UI -> EN", lambda: app._on_ui_lang("EN"))
step("jezyk UI -> PL", lambda: app._on_ui_lang("PL"))

step("jezyk tekstu -> EN", lambda: app.set_text_language("en"))
step("jezyk tekstu -> PL", lambda: app.set_text_language("pl"))

step("motyw jasny", lambda: app._on_theme(tr("theme.light")))
step("motyw ciemny", lambda: app._on_theme(tr("theme.dark")))

step("wstawienie sekcji", lambda: app._insert_section(tr("sec.chorus")))
step("migawka historii", lambda: app.panel_history.save_snapshot("test"))
step("odswiezenie historii", lambda: app.panel_history.reload())
step("podglad eksportu", lambda: app.panel_export.refresh_preview())
step("szukanie rymow", lambda: (
    app.panel_rhymes.find_entry.insert(0, "serce"),
    app.panel_rhymes.find_rhymes(),
))
step("skok do wersu", lambda: app.focus_line(3))
step("podswietlenie rymow off", lambda: app.set_rhyme_highlight(False))
step("podswietlenie rymow on", lambda: app.set_rhyme_highlight(True))
step("panel AI - etykiety", lambda: app.panel_ai.refresh_labels())
step("ustawienia - zastosowanie", lambda: app.apply_settings())

# sprzatanie: usun migawki testowe
try:
    for snap in app.history.list(app.song_key()):
        app.history.delete(snap.id)
except Exception as exc:  # noqa: BLE001
    FAILURES.append(f"sprzatanie historii: {exc}")

app._dirty = False
app.destroy()

if FAILURES:
    print(f"NIEPOWODZENIA ({len(FAILURES)}):")
    for failure in FAILURES:
        print("  -", failure)
    raise SystemExit(1)

print("Test dymny interfejsu przeszedl.")
