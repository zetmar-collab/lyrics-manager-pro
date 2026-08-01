"""Palety kolorow dla motywu jasnego i ciemnego.

CustomTkinter sam obsluguje swoje widgety; te wartosci sa potrzebne dla
surowych widgetow tkinter (edytor, rynna sylab, listy) oraz do kolorowania
grup rymow.
"""

from __future__ import annotations

import threading
import tkinter.font as tkfont

import customtkinter as ctk

# --- czcionki -------------------------------------------------------------
#
# Wspoldzielone obiekty CTkFont. Panele przebudowuja sie przy kazdym
# nacisnieciu klawisza, wiec tworzenie nowej czcionki dla kazdej etykiety
# oznaczaloby setki obiektow tkinter.font.Font na minute. Ich finalizatory
# wolaja Tcl, a gdy garbage collector uruchomi sie w watku roboczym, takie
# wywolanie zawiesza ten watek - Tk nie jest bezpieczny watkowo.

_FONT_CACHE: dict[tuple, ctk.CTkFont] = {}


def font(size: int = 12, weight: str = "normal", family: str | None = None,
         underline: bool = False) -> ctk.CTkFont:
    """Zwraca wspoldzielona czcionke o podanych parametrach."""
    key = (size, weight, family, underline)
    cached = _FONT_CACHE.get(key)
    if cached is None:
        kwargs = {"size": size, "weight": weight, "underline": underline}
        if family:
            kwargs["family"] = family
        cached = ctk.CTkFont(**kwargs)
        _FONT_CACHE[key] = cached
    return cached


def install_thread_safe_finalizers() -> None:
    """Zabezpiecza przed wywolaniem Tcl z watku innego niz glowny.

    Finalizatory `tkinter.font.Font` i `tkinter.Variable` odwoluja sie do
    interpretera Tcl. Jesli zbieracz smieci uruchomi je w watku roboczym
    (np. podczas wczytywania slownika), watek zawisa. Poza glownym watkiem
    pomijamy zwolnienie zasobu Tcl - kosztuje to nieuzywana nazwe w
    interpreterze, ale nie blokuje aplikacji.
    """
    import tkinter as tk

    def guard(cls) -> None:
        original = getattr(cls, "__del__", None)
        if original is None or getattr(original, "_lmp_guarded", False):
            return

        def safe_del(self, _original=original):
            if threading.current_thread() is threading.main_thread():
                try:
                    _original(self)
                except Exception:
                    pass

        safe_del._lmp_guarded = True
        cls.__del__ = safe_del

    guard(tkfont.Font)
    guard(tk.Variable)

LIGHT = {
    "editor_bg": "#FBFBFD",
    "editor_fg": "#16181D",
    "editor_insert": "#2563EB",
    "editor_select_bg": "#BFD8FF",
    "editor_select_fg": "#0B1020",
    "gutter_bg": "#EFF1F6",
    "gutter_fg": "#8A90A0",
    "gutter_accent": "#2563EB",
    "section_fg": "#7C3AED",
    "section_bg": "#F0EAFE",
    "current_line": "#EEF3FF",
    "muted": "#6B7280",
    "accent": "#2563EB",
    "good": "#15803D",
    "warn": "#B45309",
    "bad": "#B91C1C",
    "panel_bg": "#F2F3F7",
    "repeat_bg": "#FDE68A",
    "hard_line_bg": "#FEE2E2",
    "diff_add": "#15803D",
    "diff_del": "#B91C1C",
    "diff_meta": "#6B7280",
}

DARK = {
    "editor_bg": "#15171C",
    "editor_fg": "#E6E8EE",
    "editor_insert": "#60A5FA",
    "editor_select_bg": "#2C4A7C",
    "editor_select_fg": "#F5F7FF",
    "gutter_bg": "#1B1E25",
    "gutter_fg": "#6B7280",
    "gutter_accent": "#60A5FA",
    "section_fg": "#C4B5FD",
    "section_bg": "#2A2340",
    "current_line": "#1D2029",
    "muted": "#9AA1AF",
    "accent": "#60A5FA",
    "good": "#4ADE80",
    "warn": "#FBBF24",
    "bad": "#F87171",
    "panel_bg": "#1B1E25",
    "repeat_bg": "#4A3F1A",
    "hard_line_bg": "#43222A",
    "diff_add": "#4ADE80",
    "diff_del": "#F87171",
    "diff_meta": "#9AA1AF",
}

# Kolory grup rymow - (jasny, ciemny). Dobrane tak, by sasiednie grupy
# wyraznie sie roznily takze przy daltonizmie.
RHYME_COLORS: list[tuple[str, str]] = [
    ("#1D4ED8", "#7DA9FF"),
    ("#B91C1C", "#FF9C9C"),
    ("#047857", "#5EEAB4"),
    ("#B45309", "#FBBF24"),
    ("#7C3AED", "#C4B5FD"),
    ("#0E7490", "#67E8F9"),
    ("#BE185D", "#F9A8D4"),
    ("#4D7C0F", "#BEF264"),
    ("#7C2D12", "#FDBA74"),
    ("#3730A3", "#A5B4FC"),
    ("#831843", "#F5A9C7"),
    ("#166534", "#86EFAC"),
]


def is_dark() -> bool:
    return ctk.get_appearance_mode().lower() == "dark"


def palette() -> dict[str, str]:
    return DARK if is_dark() else LIGHT


def color(name: str) -> str:
    return palette().get(name, "#808080")


def rhyme_color(index: int) -> str:
    pair = RHYME_COLORS[index % len(RHYME_COLORS)]
    return pair[1] if is_dark() else pair[0]


# Domyslny kolor tekstu CustomTkinter (jasny, ciemny). CTk nie przyjmuje None.
DEFAULT_TEXT = ("gray10", "gray90")

# Tekst przyciskow bez wypelnienia - musi byc czytelny na obu tlach.
GHOST_TEXT = ("gray15", "gray85")


def default_text() -> tuple[str, str]:
    return DEFAULT_TEXT


def score_color(score: float) -> str:
    """Zielony / bursztyn / czerwony w zaleznosci od wyniku 0-100."""
    if score >= 70:
        return color("good")
    if score >= 45:
        return color("warn")
    return color("bad")


def apply_appearance(mode: str) -> None:
    mode = (mode or "dark").lower()
    if mode not in {"light", "dark", "system"}:
        mode = "dark"
    ctk.set_appearance_mode(mode)
