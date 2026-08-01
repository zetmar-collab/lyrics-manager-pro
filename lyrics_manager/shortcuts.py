"""Definicja skrotow klawiszowych - jedno zrodlo prawdy.

Ta sama tabela sluzy do przypisania skrotow w oknie i do wygenerowania ich
listy w instrukcji obslugi, wiec nie moga sie rozjechac.

Uwaga o Tk: widget tekstowy ma wlasne, wbudowane skroty (Ctrl+K kasuje do
konca wersu, Ctrl+O wstawia wiersz, Ctrl+E idzie na koniec wersu...). Sa one
obslugiwane *przed* skrotami okna, dlatego skroty aplikacji przypisujemy takze
bezposrednio do edytora i przerywamy tam dalsza obsluge (`editor_break`).
"""

from __future__ import annotations

from dataclasses import dataclass

# grupy w kolejnosci wyswietlania
GROUPS = ["file", "edit", "sections", "panels", "tools", "view", "help"]


@dataclass(frozen=True)
class Shortcut:
    action: str                  # klucz akcji; opis w i18n pod "key.<action>"
    label: str                   # zapis dla uzytkownika, np. "Ctrl+Shift+S"
    sequences: tuple[str, ...]   # sekwencje Tk
    group: str
    editor_break: bool = True    # przechwycic w edytorze i zatrzymac dalsza obsluge
    native: bool = False         # obsluguje sam Tk - tylko dokumentujemy


def _s(action, label, sequences, group, editor_break=True, native=False) -> Shortcut:
    return Shortcut(action, label, tuple(sequences), group, editor_break, native)


SHORTCUTS: list[Shortcut] = [
    # --- plik ------------------------------------------------------------
    _s("new", "Ctrl+N", ["<Control-n>", "<Control-N>"], "file"),
    _s("open", "Ctrl+O", ["<Control-o>", "<Control-O>"], "file"),
    _s("save", "Ctrl+S", ["<Control-s>", "<Control-S>"], "file"),
    _s("save_as", "Ctrl+Shift+S", ["<Control-Shift-S>"], "file"),
    _s("quit", "Ctrl+Q", ["<Control-q>", "<Control-Q>"], "file"),

    # --- edycja (obsluguje Tk, tylko dokumentujemy) ----------------------
    _s("undo", "Ctrl+Z", [], "edit", native=True),
    _s("redo", "Ctrl+Y", [], "edit", native=True),
    _s("cut", "Ctrl+X", [], "edit", native=True),
    _s("copy", "Ctrl+C", [], "edit", native=True),
    _s("paste", "Ctrl+V", [], "edit", native=True),
    _s("select_all", "Ctrl+A", [], "edit", native=True),
    _s("context_menu", "Prawy przycisk myszy", [], "edit", native=True),

    # --- sekcje utworu ---------------------------------------------------
    _s("section_verse", "Ctrl+Shift+V", ["<Control-Shift-V>"], "sections"),
    _s("section_chorus", "Ctrl+Shift+C", ["<Control-Shift-C>"], "sections"),
    _s("section_bridge", "Ctrl+Shift+B", ["<Control-Shift-B>"], "sections"),

    # --- panele ----------------------------------------------------------
    _s("tab_syllables", "Alt+1", ["<Alt-Key-1>"], "panels"),
    _s("tab_rhymes", "Alt+2", ["<Alt-Key-2>"], "panels"),
    _s("tab_repetitions", "Alt+3", ["<Alt-Key-3>"], "panels"),
    _s("tab_readability", "Alt+4", ["<Alt-Key-4>"], "panels"),
    _s("tab_spelling", "Alt+5", ["<Alt-Key-5>"], "panels"),
    _s("tab_ai", "Alt+6", ["<Alt-Key-6>"], "panels"),
    _s("tab_history", "Alt+7", ["<Alt-Key-7>"], "panels"),
    _s("tab_export", "Alt+8", ["<Alt-Key-8>"], "panels"),

    # --- narzedzia -------------------------------------------------------
    _s("analyze", "F5", ["<F5>", "<Control-r>", "<Control-R>"], "tools"),
    _s("spellcheck", "F7", ["<F7>", "<Control-k>", "<Control-K>"], "tools"),
    _s("dictionaries", "Ctrl+Shift+D", ["<Control-Shift-D>"], "tools"),
    _s("snapshot", "Ctrl+Shift+H", ["<Control-Shift-H>"], "tools"),
    _s("ai_run", "Ctrl+Enter", ["<Control-Return>"], "tools"),
    _s("ai_stop", "Esc", ["<Escape>"], "tools", editor_break=False),
    _s("export", "Ctrl+E", ["<Control-e>", "<Control-E>"], "tools"),
    _s("settings", "Ctrl+,", ["<Control-comma>"], "tools"),

    # --- widok -----------------------------------------------------------
    _s("toggle_theme", "Ctrl+T", ["<Control-t>", "<Control-T>"], "view"),
    _s("toggle_text_lang", "Ctrl+L", ["<Control-l>", "<Control-L>"], "view"),
    _s("toggle_ui_lang", "Ctrl+Shift+L", ["<Control-Shift-L>"], "view"),
    _s("font_bigger", "Ctrl++", ["<Control-plus>", "<Control-equal>",
                                 "<Control-KP_Add>"], "view"),
    _s("font_smaller", "Ctrl+-", ["<Control-minus>", "<Control-KP_Subtract>"], "view"),
    _s("font_reset", "Ctrl+0", ["<Control-Key-0>"], "view"),

    # --- pomoc -----------------------------------------------------------
    _s("help", "F1", ["<F1>"], "help"),
]


def by_group(group: str) -> list[Shortcut]:
    return [s for s in SHORTCUTS if s.group == group]


def bindable() -> list[Shortcut]:
    return [s for s in SHORTCUTS if s.sequences]
