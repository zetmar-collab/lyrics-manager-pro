"""Edytor tekstu piosenki: rynna z licznikiem sylab, podswietlanie rymow,
znaczniki sekcji i podswietlenie biezacego wersu.
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

import customtkinter as ctk

from ..analysis.rhymes import RhymeReport
from ..analysis.syllables import syllable_gutter
from ..analysis.text_utils import WORD_RE, is_section_marker
from . import theme


class LyricsEditor(ctk.CTkFrame):
    """Pole edycji tekstu z rynna sylab po lewej stronie."""

    def __init__(
        self,
        master,
        on_change: Callable[[], None] | None = None,
        font_family: str = "Consolas",
        font_size: int = 14,
        show_gutter: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_change = on_change
        self._text_lang = "pl"
        self._show_gutter = show_gutter
        self._suspend = False
        self._change_job: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._font = tkfont.Font(family=font_family, size=font_size)
        self._gutter_font = tkfont.Font(family=font_family, size=max(8, font_size - 2))

        self.gutter = tk.Text(
            self, width=5, padx=6, pady=10, takefocus=0, borderwidth=0,
            highlightthickness=0, font=self._gutter_font, state="disabled",
            cursor="arrow", wrap="none", spacing1=1, spacing3=1,
        )
        self.gutter.grid(row=0, column=0, sticky="ns")

        self.text = tk.Text(
            self, wrap="word", undo=True, maxundo=-1, autoseparators=True,
            borderwidth=0, highlightthickness=0, padx=14, pady=10,
            font=self._font, spacing1=1, spacing3=1, tabs="1c",
            height=10, width=40,
        )
        self.text.grid(row=0, column=1, sticky="nsew")

        self.scrollbar = ctk.CTkScrollbar(self, command=self._on_scrollbar)
        self.scrollbar.grid(row=0, column=2, sticky="ns", padx=(2, 0))
        self.text.configure(yscrollcommand=self._on_textscroll)

        self._bind_events()
        self.refresh_theme()
        self.set_gutter_visible(show_gutter)

    # -- zdarzenia --------------------------------------------------------

    def _bind_events(self) -> None:
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", lambda e: self._schedule_light_refresh())
        self.text.bind("<ButtonRelease-1>", lambda e: self._highlight_current_line())
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.gutter.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Configure>", lambda e: self._sync_gutter_scroll())
        # Ctrl+A zaznacza calosc takze na ukladzie polskim
        self.text.bind("<Control-a>", self._select_all)
        self.text.bind("<Control-A>", self._select_all)

    def _select_all(self, _event=None) -> str:
        self.text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _on_modified(self, _event=None) -> None:
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        if self._suspend:
            return
        self._schedule_light_refresh()
        if self._on_change:
            self._on_change()

    def _schedule_light_refresh(self) -> None:
        if self._change_job is not None:
            try:
                self.after_cancel(self._change_job)
            except Exception:
                pass
        self._change_job = self.after(120, self._light_refresh)

    def _light_refresh(self) -> None:
        self._change_job = None
        self.update_gutter()
        self.mark_sections()
        self._highlight_current_line()

    # -- przewijanie ------------------------------------------------------

    def _on_textscroll(self, first, last) -> None:
        self.scrollbar.set(first, last)
        self.gutter.yview_moveto(first)

    def _on_scrollbar(self, *args) -> None:
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _sync_gutter_scroll(self) -> None:
        try:
            first = self.text.yview()[0]
            self.gutter.yview_moveto(first)
        except Exception:
            pass

    def _on_mousewheel(self, event) -> str:
        delta = -1 * (event.delta // 120)
        self.text.yview_scroll(delta, "units")
        self.gutter.yview_scroll(delta, "units")
        return "break"

    # -- tresc ------------------------------------------------------------

    def get_text(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_text(self, value: str, reset_undo: bool = True) -> None:
        self._suspend = True
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        if reset_undo:
            self.text.edit_reset()
        self.text.edit_modified(False)
        self._suspend = False
        self._light_refresh()

    def get_selection(self) -> str:
        try:
            return self.text.get("sel.first", "sel.last")
        except tk.TclError:
            return ""

    def replace_selection(self, value: str) -> None:
        try:
            start = self.text.index("sel.first")
            self.text.delete("sel.first", "sel.last")
        except tk.TclError:
            start = self.text.index("insert")
        self.text.insert(start, value)
        self._light_refresh()

    def insert_at_cursor(self, value: str) -> None:
        self.text.insert("insert", value)
        self._light_refresh()

    def append_line(self, value: str) -> None:
        current = self.get_text()
        prefix = "" if not current or current.endswith("\n") else "\n"
        self.text.insert("end", prefix + value)
        self._light_refresh()

    def set_language(self, lang: str) -> None:
        self._text_lang = lang
        self.update_gutter()

    def focus_line(self, line_number: int) -> None:
        index = f"{line_number}.0"
        self.text.see(index)
        self.text.mark_set("insert", index)
        self.text.tag_remove("flash", "1.0", "end")
        self.text.tag_add("flash", index, f"{line_number}.end")
        self.after(1400, lambda: self.text.tag_remove("flash", "1.0", "end"))
        self.text.focus_set()
        self._sync_gutter_scroll()

    # -- rynna ------------------------------------------------------------

    def set_gutter_visible(self, visible: bool) -> None:
        self._show_gutter = visible
        if visible:
            self.gutter.grid(row=0, column=0, sticky="ns")
            self.update_gutter()
        else:
            self.gutter.grid_remove()

    def update_gutter(self) -> None:
        if not self._show_gutter:
            return
        labels = syllable_gutter(self.get_text(), self._text_lang)
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", "\n".join(f"{lbl:>3}" for lbl in labels))
        # kolorowanie: dlugie wersy na bursztynowo, znacznik sekcji na fioletowo
        self.gutter.tag_remove("long", "1.0", "end")
        self.gutter.tag_remove("sec", "1.0", "end")
        numeric = [int(l) for l in labels if l.isdigit()]
        avg = sum(numeric) / len(numeric) if numeric else 0
        for i, lbl in enumerate(labels, start=1):
            if lbl == "§":
                self.gutter.tag_add("sec", f"{i}.0", f"{i}.end")
            elif lbl.isdigit() and avg and int(lbl) > avg * 1.5:
                self.gutter.tag_add("long", f"{i}.0", f"{i}.end")
        self.gutter.configure(state="disabled")
        self._sync_gutter_scroll()

    # -- podswietlenia ----------------------------------------------------

    def mark_sections(self) -> None:
        self.text.tag_remove("section", "1.0", "end")
        for i, line in enumerate(self.get_text().splitlines(), start=1):
            if is_section_marker(line):
                self.text.tag_add("section", f"{i}.0", f"{i}.end")

    def _highlight_current_line(self) -> None:
        self.text.tag_remove("current", "1.0", "end")
        line = self.text.index("insert").split(".")[0]
        self.text.tag_add("current", f"{line}.0", f"{int(line) + 1}.0")
        self.text.tag_lower("current")

    def highlight_rhymes(self, report: RhymeReport | None) -> None:
        """Koloruje ostatnie slowo kazdego wersu wedlug grupy rymow."""
        for tag in self.text.tag_names():
            if tag.startswith("rhyme_"):
                self.text.tag_remove(tag, "1.0", "end")
        if report is None:
            return

        letters: dict[str, int] = {}
        for entry in report.lines:
            if entry.letter == "-" or not entry.word:
                continue
            if entry.letter not in letters:
                letters[entry.letter] = len(letters)
            idx = letters[entry.letter]
            tag = f"rhyme_{idx}"
            self.text.tag_configure(
                tag, foreground=theme.rhyme_color(idx),
                font=(self._font.actual("family"), self._font.actual("size"), "bold"),
            )
            line_text = entry.text
            pos = line_text.rfind(entry.word)
            if pos < 0:
                continue
            self.text.tag_add(tag, f"{entry.number}.{pos}",
                              f"{entry.number}.{pos + len(entry.word)}")

    def highlight_spelling(self, problems) -> None:
        """Podkresla slowa z bledem pisowni (lista obiektow Misspelling)."""
        self.text.tag_remove("misspelled", "1.0", "end")
        for problem in problems or ():
            start = f"{problem.line}.{problem.column}"
            end = f"{problem.line}.{problem.end_column}"
            self.text.tag_add("misspelled", start, end)
        # podkreslenie ma lezec nad kolorowaniem rymow, ale pod zaznaczeniem
        self.text.tag_raise("misspelled")
        self.text.tag_raise("sel")

    def clear_spelling(self) -> None:
        self.text.tag_remove("misspelled", "1.0", "end")

    def word_at_event(self, event) -> tuple[str, str, str] | None:
        """Slowo pod kursorem myszy: (slowo, indeks_poczatku, indeks_konca)."""
        index = self.text.index(f"@{event.x},{event.y}")
        line_no, col = (int(part) for part in index.split("."))
        line = self.text.get(f"{line_no}.0", f"{line_no}.end")
        if not line:
            return None
        for match in WORD_RE.finditer(line):
            if match.start() <= col < match.end():
                return (match.group(0),
                        f"{line_no}.{match.start()}",
                        f"{line_no}.{match.end()}")
        return None

    def is_misspelled_at(self, index: str) -> bool:
        return "misspelled" in self.text.tag_names(index)

    def replace_range(self, start: str, end: str, value: str) -> None:
        self.text.delete(start, end)
        self.text.insert(start, value)
        self._light_refresh()

    def replace_word_everywhere(self, old: str, new: str) -> int:
        """Zamienia wszystkie samodzielne wystapienia slowa. Zwraca ich liczbe."""
        content = self.get_text().splitlines()
        pattern = re.compile(rf"(?<![^\W\d_]){re.escape(old)}(?![^\W\d_])")
        replaced = 0
        # od konca, zeby wczesniejsze zamiany nie przesuwaly indeksow
        for line_no in range(len(content), 0, -1):
            line = content[line_no - 1]
            for match in reversed(list(pattern.finditer(line))):
                self.text.delete(f"{line_no}.{match.start()}", f"{line_no}.{match.end()}")
                self.text.insert(f"{line_no}.{match.start()}", new)
                replaced += 1
        if replaced:
            self._light_refresh()
        return replaced

    def bind_context_menu(self, handler: Callable[[object], None]) -> None:
        self.text.bind("<Button-3>", handler)

    def highlight_repeats(self, words: list[str]) -> None:
        self.text.tag_remove("repeat", "1.0", "end")
        if not words:
            return
        content = self.get_text().splitlines()
        lowered = [w.lower() for w in words]
        for i, line in enumerate(content, start=1):
            low = line.lower()
            for word in lowered:
                start = 0
                while True:
                    pos = low.find(word, start)
                    if pos < 0:
                        break
                    before_ok = pos == 0 or not low[pos - 1].isalpha()
                    after = pos + len(word)
                    after_ok = after >= len(low) or not low[after].isalpha()
                    if before_ok and after_ok:
                        self.text.tag_add("repeat", f"{i}.{pos}", f"{i}.{after}")
                    start = pos + len(word)

    def clear_repeats(self) -> None:
        self.text.tag_remove("repeat", "1.0", "end")

    # -- wyglad -----------------------------------------------------------

    def _configure_misspelled_tag(self, color: str) -> None:
        """Czerwone podkreslenie pod bledem pisowni.

        Kolor podkreslenia (`underlinefg`) doszedl w Tk 8.6.11 - na starszym
        Tk zostaje samo podkreslenie w kolorze tekstu.
        """
        try:
            self.text.tag_configure("misspelled", underline=True, underlinefg=color)
        except tk.TclError:
            self.text.tag_configure("misspelled", underline=True)

    def set_font(self, family: str, size: int) -> None:
        self._font.configure(family=family, size=size)
        self._gutter_font.configure(family=family, size=max(8, size - 2))
        self.update_gutter()

    def refresh_theme(self) -> None:
        p = theme.palette()
        self.text.configure(
            background=p["editor_bg"], foreground=p["editor_fg"],
            insertbackground=p["editor_insert"],
            selectbackground=p["editor_select_bg"], selectforeground=p["editor_select_fg"],
        )
        self.gutter.configure(
            background=p["gutter_bg"], foreground=p["gutter_fg"],
            selectbackground=p["gutter_bg"], selectforeground=p["gutter_fg"],
            insertbackground=p["gutter_bg"],
        )
        self.gutter.tag_configure("sec", foreground=p["section_fg"])
        self.gutter.tag_configure("long", foreground=p["warn"])
        self.text.tag_configure("section", foreground=p["section_fg"],
                                background=p["section_bg"])
        self.text.tag_configure("current", background=p["current_line"])
        self.text.tag_configure("repeat", background=p["repeat_bg"])
        self.text.tag_configure("flash", background=p["editor_select_bg"])
        self._configure_misspelled_tag(p["bad"])
        self.text.tag_lower("current")
        self.update_gutter()
        self.mark_sections()


class ReadOnlyText(ctk.CTkFrame):
    """Prosty panel tekstowy tylko do odczytu (raporty, podglady, diff)."""

    def __init__(self, master, font_family: str = "Consolas", font_size: int = 12, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._font = tkfont.Font(family=font_family, size=font_size)
        # height/width w znakach: tk.Text domyslnie zada 24 wierszy i 80 kolumn,
        # co rozpycha panel i zgniata sasiednie elementy.
        self.text = tk.Text(
            self, wrap="word", borderwidth=0, highlightthickness=0,
            padx=12, pady=10, font=self._font, state="disabled", cursor="arrow",
            height=6, width=20,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ctk.CTkScrollbar(self, command=self.text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.text.bind("<MouseWheel>", self._wheel)
        self.refresh_theme()

    def _wheel(self, event) -> str:
        self.text.yview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def set_content(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.configure(state="disabled")

    def set_diff(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for line in value.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                tag = "add"
            elif line.startswith("-") and not line.startswith("---"):
                tag = "del"
            elif line.startswith("@@") or line.startswith("+++") or line.startswith("---"):
                tag = "meta"
            else:
                tag = ""
            self.text.insert("end", line + "\n", tag)
        self.text.configure(state="disabled")

    def append(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", value)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self) -> None:
        self.set_content("")

    def get_content(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_font_size(self, size: int) -> None:
        self._font.configure(size=size)

    def refresh_theme(self) -> None:
        p = theme.palette()
        self.text.configure(
            background=p["editor_bg"], foreground=p["editor_fg"],
            selectbackground=p["editor_select_bg"], selectforeground=p["editor_select_fg"],
            insertbackground=p["editor_bg"],
        )
        self.text.tag_configure("add", foreground=p["diff_add"])
        self.text.tag_configure("del", foreground=p["diff_del"])
        self.text.tag_configure("meta", foreground=p["diff_meta"])
