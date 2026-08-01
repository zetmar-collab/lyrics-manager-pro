"""Glowne okno aplikacji Lyrics Manager Pro."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from .. import APP_NAME, APP_VERSION
from ..analysis.rhymes import RhymeReport
from ..config import Config
from ..document import FILE_EXT, Document
from ..history import HistoryStore, song_key
from ..i18n import LANGUAGE_LABELS, get_ui_language, set_ui_language, tr
from ..shortcuts import bindable
from ..spelling import PersonalDictionary, SpellChecker, default_code_for, installed_codes
from . import theme
from .ai_panel import AIPanel
from .editor import LyricsEditor
from .export_panel import ExportPanel
from .help_window import HelpWindow
from .history_panel import HistoryPanel
from .panels import ReadabilityPanel, RepetitionPanel, RhymePanel, SyllablePanel
from .settings_dialog import SettingsDialog
from .spell_panel import SpellPanel
from .widgets import TabView, Toolbar, make_segmented

SECTIONS = ["intro", "verse", "prechorus", "chorus", "bridge", "outro"]
SECTION_TAGS = {
    "intro": "Intro", "verse": "Verse", "prechorus": "Pre-Chorus",
    "chorus": "Chorus", "bridge": "Bridge", "outro": "Outro",
}

FILE_TYPES = [
    ("Lyrics Manager Pro", f"*{FILE_EXT}"),
    ("Text", "*.txt"),
    ("Markdown", "*.md"),
    ("All files", "*.*"),
]


class LyricsManagerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        theme.install_thread_safe_finalizers()

        self.config_store = Config()
        set_ui_language(self.config_store.get("ui_language", "pl"))
        theme.apply_appearance(self.config_store.get("theme", "dark"))
        ctk.set_default_color_theme(self.config_store.get("color_theme", "blue"))

        self.document = Document(text_language=self.config_store.get("text_language", "pl"))
        self.history = HistoryStore()
        self.last_rhyme_report: RhymeReport | None = None

        self.spell = SpellChecker(PersonalDictionary())
        self._spell_state = "off"
        self._spell_report = None
        self._spell_suggestions: dict[str, list[str]] = {}
        self._spell_loading: set[str] = set()
        self._spell_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._spell_job: str | None = None

        self._help_window: HelpWindow | None = None

        self._dirty = False
        self._analysis_job: str | None = None
        self._autosave_job: str | None = None
        self._status_job: str | None = None

        self.title(APP_NAME)
        self._apply_geometry(self.config_store.get("window_geometry", "1360x860"))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_toolbar()
        self._build_meta_bar()
        self._build_body()
        self._build_statusbar()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._bind_shortcuts()

        self.editor.bind_context_menu(self._on_editor_context)
        self._poll_spell_queue()

        self.apply_settings()
        self.request_analysis(force=True)
        self.request_spellcheck(force=True)
        self.reschedule_autosave()
        self.set_status(tr("app.ready"))

    def _apply_geometry(self, saved: str) -> None:
        """Ustawia rozmiar okna, nie pozwalajac mu wyjsc poza ekran.

        Zapisana geometria moze pochodzic z wiekszego monitora - wtedy okno
        chowaloby sie pod paskiem zadan albo poza krawedzia ekranu.
        """
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        # zapas na pasek zadan i ramke okna
        max_w = max(800, screen_w - 40)
        max_h = max(560, screen_h - 90)

        width, height = 1360, 860
        try:
            size = saved.split("+")[0]
            width, height = (int(v) for v in size.lower().split("x"))
        except (ValueError, AttributeError):
            pass

        width = min(width, max_w)
        height = min(height, max_h)
        self.minsize(min(1080, max_w), min(680, max_h))

        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height - 60) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ==================================================================
    # BUDOWA INTERFEJSU
    # ==================================================================

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        left = Toolbar(bar)
        left.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        self.btn_new = left.add(ctk.CTkButton(left, text=tr("tb.new"), width=80,
                                              command=self.new_document))
        self.btn_open = left.add(ctk.CTkButton(left, text=tr("tb.open"), width=80,
                                               command=self.open_document))
        self.btn_save = left.add(ctk.CTkButton(left, text=tr("tb.save"), width=80,
                                               command=self.save_document))
        self.btn_save_as = left.add(ctk.CTkButton(
            left, text=tr("tb.save_as"), width=100, fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
            command=lambda: self.save_document(save_as=True)))

        sep = ctk.CTkLabel(left, text="│", text_color=theme.color("muted"))
        left.add(sep, padx=(6, 6))

        self.section_menu = left.add(ctk.CTkOptionMenu(
            left, values=[tr("sec.insert")] + [tr(f"sec.{s}") for s in SECTIONS],
            width=150, command=self._insert_section,
        ))
        self.section_menu.set(tr("sec.insert"))

        right = Toolbar(bar)
        right.grid(row=0, column=1, sticky="e", padx=10, pady=8)

        self.lbl_ui_lang = right.add(ctk.CTkLabel(right, text=tr("tb.ui_lang"),
                                                  font=theme.font(size=11)), padx=(0, 4))
        self.ui_lang_menu = right.add(make_segmented(
            right, values=["PL", "EN"], width=90, command=self._on_ui_lang,
        ), padx=(0, 12))
        self.ui_lang_menu.set(get_ui_language().upper())

        self.lbl_text_lang = right.add(ctk.CTkLabel(right, text=tr("tb.text_lang"),
                                                    font=theme.font(size=11)), padx=(0, 4))
        self.text_lang_menu = right.add(make_segmented(
            right, values=["PL", "EN"], width=90, command=self._on_text_lang,
        ), padx=(0, 12))
        self.text_lang_menu.set(self.document.text_language.upper())

        self.lbl_theme = right.add(ctk.CTkLabel(right, text=tr("tb.theme"),
                                                font=theme.font(size=11)), padx=(0, 4))
        self.theme_menu = right.add(make_segmented(
            right, values=self._theme_values(), width=150, command=self._on_theme,
        ), padx=(0, 12))
        self.theme_menu.set(tr("theme.dark") if theme.is_dark() else tr("theme.light"))

        self.btn_settings = right.add(ctk.CTkButton(
            right, text=tr("tb.settings"), width=110, fg_color="transparent",
            border_width=1, text_color=theme.GHOST_TEXT, command=self.open_settings,
        ), padx=(0, 6))

        self.btn_help = right.add(ctk.CTkButton(
            right, text=f"{tr('tb.help')}  (F1)", width=110, fg_color="transparent",
            border_width=1, text_color=theme.GHOST_TEXT, command=self.open_help,
        ), padx=0)

    def _build_meta_bar(self) -> None:
        bar = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(6, 0))
        for c in (1, 3, 5):
            bar.grid_columnconfigure(c, weight=1)

        self.meta_title_lbl = ctk.CTkLabel(bar, text=tr("meta.title"),
                                           font=theme.font(size=11))
        self.meta_title_lbl.grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.meta_title = ctk.CTkEntry(bar, width=200)
        self.meta_title.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        self.meta_artist_lbl = ctk.CTkLabel(bar, text=tr("meta.artist"),
                                            font=theme.font(size=11))
        self.meta_artist_lbl.grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.meta_artist = ctk.CTkEntry(bar, width=160)
        self.meta_artist.grid(row=0, column=3, sticky="ew", padx=(0, 12))

        self.meta_style_lbl = ctk.CTkLabel(bar, text=tr("meta.style"),
                                           font=theme.font(size=11))
        self.meta_style_lbl.grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.meta_style = ctk.CTkEntry(
            bar, placeholder_text="indie folk, acoustic guitar, female vocal")
        self.meta_style.grid(row=0, column=5, sticky="ew", padx=(0, 12))

        self.meta_tempo_lbl = ctk.CTkLabel(bar, text=tr("meta.tempo"),
                                           font=theme.font(size=11))
        self.meta_tempo_lbl.grid(row=0, column=6, sticky="w", padx=(0, 4))
        self.meta_tempo = ctk.CTkEntry(bar, width=70)
        self.meta_tempo.grid(row=0, column=7, sticky="w", padx=(0, 12))

        self.meta_key_lbl = ctk.CTkLabel(bar, text=tr("meta.key"),
                                         font=theme.font(size=11))
        self.meta_key_lbl.grid(row=0, column=8, sticky="w", padx=(0, 4))
        self.meta_key = ctk.CTkEntry(bar, width=70)
        self.meta_key.grid(row=0, column=9, sticky="w")

        for entry in (self.meta_title, self.meta_artist, self.meta_style,
                      self.meta_tempo, self.meta_key):
            entry.bind("<KeyRelease>", lambda e: self._on_meta_change())

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=10, pady=8)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=3, minsize=520)
        body.grid_columnconfigure(1, weight=2, minsize=420)

        editor_card = ctk.CTkFrame(body)
        editor_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        editor_card.grid_rowconfigure(0, weight=1)
        editor_card.grid_columnconfigure(0, weight=1)

        self.editor = LyricsEditor(
            editor_card,
            on_change=self._on_text_change,
            font_family=self.config_store.get("editor_font_family", "Consolas"),
            font_size=int(self.config_store.get("editor_font_size", 14)),
            show_gutter=bool(self.config_store.get("show_syllable_gutter", True)),
        )
        self.editor.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.editor.set_language(self.document.text_language)

        self.tabs = TabView(body, columns=4)
        self.tabs.grid(row=0, column=1, sticky="nsew")

        self._tab_order = ["syllables", "rhymes", "repetitions", "readability",
                           "spelling", "ai", "history", "export"]
        factories = {
            "syllables": lambda p: SyllablePanel(p, self),
            "rhymes": lambda p: RhymePanel(p, self),
            "repetitions": lambda p: RepetitionPanel(p, self),
            "readability": lambda p: ReadabilityPanel(p, self),
            "spelling": lambda p: SpellPanel(p, self),
            "ai": lambda p: AIPanel(p, self),
            "history": lambda p: HistoryPanel(p, self),
            "export": lambda p: ExportPanel(p, self),
        }
        self._panels = {
            name: self.tabs.add(name, tr(f"tab.{name}"), factories[name])
            for name in self._tab_order
        }
        self.tabs.set_change_callback(self._on_tab_change)

        self.panel_syllables = self._panels["syllables"]
        self.panel_rhymes = self._panels["rhymes"]
        self.panel_repetition = self._panels["repetitions"]
        self.panel_readability = self._panels["readability"]
        self.panel_spelling = self._panels["spelling"]
        self.panel_ai = self._panels["ai"]
        self.panel_history = self._panels["history"]
        self.panel_export = self._panels["export"]

        self.panel_rhymes.highlight_var.set(
            bool(self.config_store.get("highlight_rhymes", True))
        )

    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(self, corner_radius=0, height=28)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(bar, text="", anchor="w",
                                         font=theme.font(size=11))
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=4)

        self.doc_label = ctk.CTkLabel(bar, text="", anchor="e",
                                      text_color=theme.color("muted"),
                                      font=theme.font(size=11))
        self.doc_label.grid(row=0, column=1, sticky="e", padx=12, pady=4)

        self.version_label = ctk.CTkLabel(bar, text=f"v{APP_VERSION}", anchor="e",
                                          text_color=theme.color("muted"),
                                          font=theme.font(size=11))
        self.version_label.grid(row=0, column=2, sticky="e", padx=(0, 12), pady=4)

    def _shortcut_actions(self) -> dict[str, Callable[[], None]]:
        """Mapowanie akcji z tabeli skrotow na metody okna."""
        actions: dict[str, Callable[[], None]] = {
            "new": self.new_document,
            "open": self.open_document,
            "save": self.save_document,
            "save_as": lambda: self.save_document(save_as=True),
            "quit": self.on_close,
            "section_verse": lambda: self._insert_section(tr("sec.verse")),
            "section_chorus": lambda: self._insert_section(tr("sec.chorus")),
            "section_bridge": lambda: self._insert_section(tr("sec.bridge")),
            "analyze": lambda: self.request_analysis(force=True),
            "spellcheck": lambda: self.request_spellcheck(force=True),
            "dictionaries": self._open_dictionaries,
            "snapshot": self.panel_history.save_snapshot,
            "ai_run": self._run_ai,
            "ai_stop": self._stop_ai,
            "export": lambda: self.tabs.select("export"),
            "settings": self.open_settings,
            "toggle_theme": self._toggle_theme,
            "toggle_text_lang": self._toggle_text_language,
            "toggle_ui_lang": self._toggle_ui_language,
            "font_bigger": lambda: self._change_font_size(1),
            "font_smaller": lambda: self._change_font_size(-1),
            "font_reset": lambda: self._change_font_size(0),
            "help": self.open_help,
        }
        for name in self._tab_order:
            actions[f"tab_{name}"] = lambda n=name: self.tabs.select(n)
        return actions

    def _bind_shortcuts(self) -> None:
        actions = self._shortcut_actions()

        for shortcut in bindable():
            callback = actions.get(shortcut.action)
            if callback is None:
                continue

            def handler(_event=None, cb=callback, stop=shortcut.editor_break):
                cb()
                # "break" zatrzymuje wbudowana obsluge widgetu tekstowego,
                # ktora inaczej wykonalaby swoja akcje (Ctrl+K kasuje wers itd.)
                return "break" if stop else None

            for sequence in shortcut.sequences:
                self.bind(sequence, handler)
                if shortcut.editor_break:
                    # w edytorze wiazemy bezposrednio: powiazania widgetu maja
                    # pierwszenstwo przed powiazaniami klasy Text
                    self.editor.text.bind(sequence, handler)

    # -- akcje skrotow ----------------------------------------------------

    def _open_dictionaries(self) -> None:
        self.tabs.select("spelling")
        self.panel_spelling.open_manager()

    def _run_ai(self) -> None:
        self.tabs.select("ai")
        self.panel_ai.run()

    def _stop_ai(self) -> None:
        self.panel_ai.stop()

    def _toggle_theme(self) -> None:
        self._on_theme(tr("theme.light") if theme.is_dark() else tr("theme.dark"))

    def _toggle_text_language(self) -> None:
        self.set_text_language("en" if self.text_language() == "pl" else "pl")

    def _toggle_ui_language(self) -> None:
        self._on_ui_lang("EN" if get_ui_language() == "pl" else "PL")

    def _change_font_size(self, delta: int) -> None:
        current = int(self.config_store.get("editor_font_size", 14))
        size = 14 if delta == 0 else max(9, min(28, current + delta))
        self.config_store.set("editor_font_size", size)
        self.editor.set_font(self.config_store.get("editor_font_family", "Consolas"), size)
        self.set_status(f"{tr('set.font_size')}: {size}", kind="ok")

    def open_help(self) -> None:
        if self._help_window is not None and self._help_window.winfo_exists():
            self._help_window.lift()
            self._help_window.focus_force()
            return
        self._help_window = HelpWindow(self, self)

    # ==================================================================
    # API DLA PANELI
    # ==================================================================

    @property
    def settings(self) -> Config:
        """Ustawienia aplikacji. Nazwa `settings`, a nie `config`, bo `config`
        to metoda tkintera i nadpisanie jej psuje widgety."""
        return self.config_store

    def get_text(self) -> str:
        return self.editor.get_text()

    def set_text(self, value: str) -> None:
        self.editor.set_text(value)
        self._mark_dirty()
        self.request_analysis(force=True)

    def get_selection(self) -> str:
        return self.editor.get_selection()

    def replace_selection(self, value: str) -> None:
        if not self.editor.get_selection():
            self.set_status(tr("msg.no_selection"), kind="warn")
            return
        self.editor.replace_selection(value)
        self._mark_dirty()
        self.request_analysis(force=True)

    def insert_text(self, value: str) -> None:
        self.editor.insert_at_cursor(value)
        self._mark_dirty()
        self.request_analysis()

    def focus_line(self, number: int) -> None:
        self.editor.focus_line(number)

    def text_language(self) -> str:
        return self.document.text_language

    def song_key(self) -> str:
        return song_key(self.document.path, self.document.meta.title)

    def copy_to_clipboard(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update_idletasks()

    def set_rhyme_highlight(self, enabled: bool) -> None:
        self.config_store.set("highlight_rhymes", enabled)
        self.editor.highlight_rhymes(self.last_rhyme_report if enabled else None)

    def highlight_repeats(self, words: list[str]) -> None:
        if self.tabs.get() == "repetitions":
            self.editor.highlight_repeats(words)
        else:
            self.editor.clear_repeats()

    def _on_tab_change(self, name: str) -> None:
        # zolte podswietlenie powtorzen ma sens tylko na wlasnej zakladce
        if name != "repetitions":
            self.editor.clear_repeats()

        if name == "export":
            self.panel_export.refresh_preview()
        elif name == "history":
            self.panel_history.reload()
        elif name == "repetitions":
            self.panel_repetition.update_report(self.get_text(), self.text_language())

    def request_ai_rhymes(self, word: str) -> None:
        target = word or ""
        if not target:
            selection = self.get_selection().strip()
            target = selection.split()[-1] if selection else ""
        if not target:
            self.set_status(tr("msg.no_selection"), kind="warn")
            return
        self.tabs.select("ai")
        self.panel_ai.run_rhyme_task(target)

    # ==================================================================
    # ANALIZA
    # ==================================================================

    def _on_text_change(self) -> None:
        self._mark_dirty()
        if self.config_store.get("live_analysis", True):
            self.request_analysis()

    def request_analysis(self, force: bool = False) -> None:
        if self._analysis_job is not None:
            try:
                self.after_cancel(self._analysis_job)
            except Exception:
                pass
        delay = 10 if force else 450
        self._analysis_job = self.after(delay, self._run_analysis)

    def _run_analysis(self) -> None:
        self._analysis_job = None
        self.request_spellcheck()
        text = self.get_text()
        lang = self.document.text_language

        self.panel_syllables.update_report(text, lang)
        self.panel_rhymes.update_report(text, lang)
        self.panel_repetition.update_report(text, lang)
        self.panel_readability.update_report(text, lang)
        self.panel_export.refresh_preview()

        if self.config_store.get("highlight_rhymes", True):
            self.editor.highlight_rhymes(self.last_rhyme_report)
        else:
            self.editor.highlight_rhymes(None)

        self._update_doc_label()

    # ==================================================================
    # PISOWNIA
    # ==================================================================

    def spell_code(self) -> str | None:
        """Kod slownika uzywanego dla biezacego jezyka tekstu."""
        lang = self.text_language()
        codes = installed_codes()
        saved = self.config_store.get(f"spell_dict_{lang}", "")
        if saved and saved in codes:
            return saved
        return default_code_for(lang, codes)

    def set_spell_dictionary(self, code: str) -> None:
        self.config_store.set(f"spell_dict_{self.text_language()}", code)
        self.reload_spell_dictionary()

    def release_spell_dictionary(self, code: str) -> None:
        """Zwalnia slownik z pamieci - konieczne przed usunieciem plikow."""
        self.spell.unload(code)
        self._spell_suggestions.clear()

    def reload_spell_dictionary(self) -> None:
        self._spell_suggestions.clear()
        self.panel_spelling.refresh_dictionary_list()
        self.request_spellcheck(force=True)

    def request_spellcheck(self, force: bool = False) -> None:
        if self._spell_job is not None:
            try:
                self.after_cancel(self._spell_job)
            except Exception:
                pass
        self._spell_job = self.after(20 if force else 600, self._run_spellcheck)

    def _run_spellcheck(self) -> None:
        self._spell_job = None

        if not self.config_store.get("spell_check_enabled", True):
            self._set_spell_state("off")
            return
        if not SpellChecker.engine_available():
            self._set_spell_state("no_engine")
            return

        code = self.spell_code()
        if not code:
            self._set_spell_state("missing")
            return

        if not self.spell.is_loaded(code):
            if code not in self._spell_loading:
                self._spell_loading.add(code)
                threading.Thread(target=self._load_dictionary, args=(code,),
                                 daemon=True).start()
            self._set_spell_state("loading")
            return

        report = self.spell.check_text(self.get_text(), code, self.text_language())
        self._spell_report = report
        self._spell_state = "ready"
        self.editor.highlight_spelling(report.problems)
        self.panel_spelling.update_report(report, "ready")
        self._prefetch_suggestions(report, code)

    def _load_dictionary(self, code: str) -> None:
        try:
            self.spell.load(code)
            self._spell_queue.put(("loaded", code))
        except Exception as exc:  # noqa: BLE001 - komunikat trafia do panelu
            self._spell_queue.put(("load_failed", (code, exc)))

    def _set_spell_state(self, state: str) -> None:
        self._spell_state = state
        self._spell_report = None
        self.editor.clear_spelling()
        self.panel_spelling.update_report(None, state)

    def _prefetch_suggestions(self, report, code: str, limit: int = 15) -> None:
        """Liczy podpowiedzi w tle - dla polskiego potrafi to zajac sekundy,
        wiec menu kontekstowe nie moze na to czekac."""
        wanted = [w for w, _ in report.unique[:limit]
                  if w not in self._spell_suggestions]
        if not wanted:
            return

        def work() -> None:
            for word in wanted:
                found = self.spell.suggest(word, code)
                self._spell_queue.put(("suggestions", (word, found)))

        threading.Thread(target=work, daemon=True).start()

    def _poll_spell_queue(self) -> None:
        try:
            while True:
                kind, payload = self._spell_queue.get_nowait()
                if kind == "loaded":
                    self._spell_loading.discard(payload)
                    self.request_spellcheck(force=True)
                elif kind == "load_failed":
                    code, exc = payload
                    self._spell_loading.discard(code)
                    self._set_spell_state("missing")
                    self.set_status(f"{tr('msg.error')}: {exc}", kind="error")
                elif kind == "suggestions":
                    word, found = payload
                    self._spell_suggestions[word] = found
        except queue.Empty:
            pass
        self.after(150, self._poll_spell_queue)

    # -- menu kontekstowe -------------------------------------------------

    def _on_editor_context(self, event) -> str:
        found = self.editor.word_at_event(event)
        menu = tk.Menu(self, tearoff=0)
        palette = theme.palette()
        menu.configure(
            background=palette["panel_bg"], foreground=palette["editor_fg"],
            activebackground=palette["accent"], activeforeground="#FFFFFF",
            borderwidth=0, activeborderwidth=0,
        )

        if found:
            word, start, end = found
            code = self.spell_code()
            misspelled = self.editor.is_misspelled_at(start)

            if misspelled and code:
                suggestions = self._spell_suggestions.get(word)
                if suggestions is None:
                    menu.add_command(label=tr("sp.searching"), state="disabled")
                    self._spell_suggestions[word] = []
                    threading.Thread(
                        target=lambda: self._spell_queue.put(
                            ("suggestions", (word, self.spell.suggest(word, code)))),
                        daemon=True,
                    ).start()
                elif not suggestions:
                    menu.add_command(label=tr("sp.no_suggestions"), state="disabled")
                else:
                    for candidate in suggestions:
                        menu.add_command(
                            label=candidate,
                            command=lambda c=candidate, s=start, e=end:
                                self._apply_correction(s, e, c),
                        )
                    menu.add_separator()
                    menu.add_command(
                        label=tr("sp.replace_all"),
                        command=lambda w=word, c=suggestions[0]:
                            self._replace_everywhere(w, c),
                    )
                menu.add_separator()
                menu.add_command(label=tr("sp.add_to_dict"),
                                 command=lambda w=word: self._add_to_dictionary(w))
                menu.add_command(label=tr("sp.ignore"),
                                 command=lambda w=word: self._ignore_word(w))
                menu.add_separator()

            menu.add_command(label=tr("rhy.find_for"),
                             command=lambda w=word: self._find_rhymes_for(w))

        menu.add_separator()
        menu.add_command(label=tr("ai.copy"), command=lambda: self._copy_selection())
        menu.add_command(label=tr("sp.recheck"),
                         command=lambda: self.request_spellcheck(force=True))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _apply_correction(self, start: str, end: str, replacement: str) -> None:
        self.editor.replace_range(start, end, replacement)
        self._mark_dirty()
        self.request_analysis(force=True)

    def _replace_everywhere(self, word: str, replacement: str) -> None:
        count = self.editor.replace_word_everywhere(word, replacement)
        if count:
            self._mark_dirty()
            self.request_analysis(force=True)
            self.set_status(f"{word} → {replacement}  ({count}×)", kind="ok")

    def _add_to_dictionary(self, word: str) -> None:
        code = self.spell_code()
        if not code:
            return
        self.spell.add_to_personal(word, self.text_language(), code)
        self._spell_suggestions.pop(word, None)
        self.request_spellcheck(force=True)
        self.set_status(tr("sp.add_to_dict") + f": {word}", kind="ok")

    def _ignore_word(self, word: str) -> None:
        code = self.spell_code()
        if not code:
            return
        self.spell.ignore(word, code)
        self.request_spellcheck(force=True)

    def _find_rhymes_for(self, word: str) -> None:
        self.tabs.select("rhymes")
        self.panel_rhymes.find_entry.delete(0, "end")
        self.panel_rhymes.find_entry.insert(0, word)
        self.panel_rhymes.find_rhymes()

    def _copy_selection(self) -> None:
        selection = self.get_selection()
        if selection:
            self.copy_to_clipboard(selection)

    # ==================================================================
    # DOKUMENT
    # ==================================================================

    def _mark_dirty(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._update_doc_label()

    def _on_meta_change(self) -> None:
        self._sync_meta_from_form()
        self._mark_dirty()
        self.panel_export.refresh_preview()

    def _sync_meta_from_form(self) -> None:
        meta = self.document.meta
        meta.title = self.meta_title.get()
        meta.artist = self.meta_artist.get()
        meta.style = self.meta_style.get()
        meta.tempo = self.meta_tempo.get()
        meta.key = self.meta_key.get()

    def _sync_form_from_meta(self) -> None:
        pairs = [
            (self.meta_title, self.document.meta.title),
            (self.meta_artist, self.document.meta.artist),
            (self.meta_style, self.document.meta.style),
            (self.meta_tempo, self.document.meta.tempo),
            (self.meta_key, self.document.meta.key),
        ]
        for entry, value in pairs:
            entry.delete(0, "end")
            entry.insert(0, value or "")

    def _update_doc_label(self) -> None:
        name = self.document.filename or tr("app.untitled")
        state = f" · {tr('app.modified')}" if self._dirty else ""
        self.doc_label.configure(text=f"{name}{state}")
        title = self.document.display_title
        self.title(f"{title + ' — ' if title else ''}{APP_NAME}")

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        return messagebox.askyesno(tr("msg.question"), tr("msg.confirm_new"), parent=self)

    def new_document(self) -> None:
        if not self._confirm_discard():
            return
        self._snapshot_now(tr("hist.auto"))
        self.document = Document(text_language=self.document.text_language)
        self._sync_form_from_meta()
        self.editor.set_text("")
        self._dirty = False
        self.panel_history.reload()
        self.request_analysis(force=True)
        self.set_status(tr("app.ready"))

    def open_document(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            parent=self, title=tr("tb.open"), filetypes=FILE_TYPES,
            initialdir=self.config_store.get("last_directory") or None,
        )
        if not path:
            return
        self.open_path(path)

    def open_path(self, path: str) -> None:
        """Wczytuje utwor z pliku - takze przekazanego w wierszu polecen."""
        try:
            document = Document.load(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror(tr("msg.error"), tr("msg.open_failed", err=exc), parent=self)
            return

        self.document = document
        self.config_store.set("last_directory", str(Path(path).parent))
        self._sync_form_from_meta()
        self.editor.set_text(document.text)
        self.set_text_language(document.text_language)
        self._dirty = False
        self.panel_history.reload()
        self.request_analysis(force=True)
        self.set_status(tr("msg.file_opened", path=path), kind="ok")

    def save_document(self, save_as: bool = False) -> None:
        self._sync_meta_from_form()
        self.document.text = self.get_text()

        path = self.document.path
        if save_as or not path:
            base = self.document.display_title or tr("app.untitled")
            safe = "".join(ch for ch in base if ch not in '<>:"/\\|?*').strip() or "lyrics"
            path = filedialog.asksaveasfilename(
                parent=self, title=tr("tb.save"), defaultextension=FILE_EXT,
                initialfile=f"{safe}{FILE_EXT}", filetypes=FILE_TYPES,
                initialdir=self.config_store.get("last_directory") or None,
            )
            if not path:
                return

        try:
            saved = self.document.save(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror(tr("msg.error"), tr("msg.save_failed", err=exc), parent=self)
            return

        self.config_store.set("last_directory", str(Path(saved).parent))
        self._dirty = False
        self._snapshot_now(tr("app.saved"))
        self.panel_history.reload()
        self._update_doc_label()
        self.set_status(tr("msg.file_saved", path=saved), kind="ok")

    def _snapshot_now(self, label: str) -> None:
        text = self.get_text()
        if text.strip():
            self.history.add(self.song_key(), text, label, "auto")
            self.history.prune(self.song_key())

    # ==================================================================
    # AUTOZAPIS HISTORII
    # ==================================================================

    def reschedule_autosave(self) -> None:
        if self._autosave_job is not None:
            try:
                self.after_cancel(self._autosave_job)
            except Exception:
                pass
            self._autosave_job = None
        minutes = int(self.config_store.get("history_autosave_minutes", 5) or 0)
        if minutes <= 0:
            return
        self._autosave_job = self.after(minutes * 60_000, self._autosave_tick)

    def _autosave_tick(self) -> None:
        self._autosave_job = None
        text = self.get_text()
        if text.strip():
            snap = self.history.add(self.song_key(), text, tr("hist.auto"), "auto")
            if snap:
                self.history.prune(self.song_key())
                self.panel_history.reload()
        self.reschedule_autosave()

    # ==================================================================
    # JEZYK, MOTYW, USTAWIENIA
    # ==================================================================

    def _theme_values(self) -> list[str]:
        return [tr("theme.light"), tr("theme.dark")]

    def _on_ui_lang(self, value: str) -> None:
        lang = value.lower()
        self.ui_lang_menu.set(lang.upper())
        if lang == get_ui_language():
            return
        set_ui_language(lang)
        self.config_store.set("ui_language", lang)
        self.config_store.save()
        self.refresh_labels()

    def _on_text_lang(self, value: str) -> None:
        self.set_text_language(value.lower())

    def set_text_language(self, lang: str) -> None:
        lang = lang if lang in ("pl", "en") else "pl"
        self.document.text_language = lang
        self.config_store.set("text_language", lang)
        self.text_lang_menu.set(lang.upper())
        self.editor.set_language(lang)
        self.request_analysis(force=True)
        self.request_spellcheck(force=True)

    def _on_theme(self, value: str) -> None:
        mode = "dark" if value == tr("theme.dark") else "light"
        theme.apply_appearance(mode)
        self.config_store.set("theme", mode)
        self.config_store.save()
        self.refresh_theme()

    def refresh_labels(self) -> None:
        """Przebudowuje wszystkie napisy po zmianie jezyka interfejsu."""
        self.btn_new.configure(text=tr("tb.new"))
        self.btn_open.configure(text=tr("tb.open"))
        self.btn_save.configure(text=tr("tb.save"))
        self.btn_save_as.configure(text=tr("tb.save_as"))
        self.btn_settings.configure(text=tr("tb.settings"))
        self.btn_help.configure(text=f"{tr('tb.help')}  (F1)")
        if self._help_window is not None and self._help_window.winfo_exists():
            self._help_window.refresh_labels()
        self.lbl_ui_lang.configure(text=tr("tb.ui_lang"))
        self.lbl_text_lang.configure(text=tr("tb.text_lang"))
        self.lbl_theme.configure(text=tr("tb.theme"))
        self.ui_lang_menu.set(get_ui_language().upper())
        self.theme_menu.configure(values=self._theme_values())
        self.theme_menu.set(tr("theme.dark") if theme.is_dark() else tr("theme.light"))

        self.section_menu.configure(
            values=[tr("sec.insert")] + [tr(f"sec.{s}") for s in SECTIONS]
        )
        self.section_menu.set(tr("sec.insert"))

        self.meta_title_lbl.configure(text=tr("meta.title"))
        self.meta_artist_lbl.configure(text=tr("meta.artist"))
        self.meta_style_lbl.configure(text=tr("meta.style"))
        self.meta_tempo_lbl.configure(text=tr("meta.tempo"))
        self.meta_key_lbl.configure(text=tr("meta.key"))

        for name in self._tab_order:
            self.tabs.set_label(name, tr(f"tab.{name}"))

        for panel in self._panels.values():
            if hasattr(panel, "refresh_labels"):
                panel.refresh_labels()

        self._update_doc_label()
        self.request_analysis(force=True)
        self.set_status(tr("app.ready"))

    def refresh_theme(self) -> None:
        self.editor.refresh_theme()
        for panel in self._panels.values():
            if hasattr(panel, "refresh_theme"):
                panel.refresh_theme()
        self.tabs.refresh_theme()
        if self._help_window is not None and self._help_window.winfo_exists():
            self._help_window.refresh_theme()
        self.doc_label.configure(text_color=theme.color("muted"))
        self.version_label.configure(text_color=theme.color("muted"))
        self.editor.highlight_rhymes(
            self.last_rhyme_report if self.config_store.get("highlight_rhymes", True) else None
        )
        self.request_analysis(force=True)

    def apply_settings(self) -> None:
        self.editor.set_font(
            self.config_store.get("editor_font_family", "Consolas"),
            int(self.config_store.get("editor_font_size", 14)),
        )
        self.editor.set_gutter_visible(
            bool(self.config_store.get("show_syllable_gutter", True))
        )
        self.panel_rhymes.highlight_var.set(
            bool(self.config_store.get("highlight_rhymes", True))
        )
        self.reschedule_autosave()
        self.request_analysis(force=True)

    def open_settings(self) -> None:
        SettingsDialog(self, self)

    # ==================================================================
    # POZOSTALE
    # ==================================================================

    def _insert_section(self, value: str) -> None:
        for key in SECTIONS:
            if tr(f"sec.{key}") == value:
                tag = SECTION_TAGS[key]
                current = self.get_text()
                prefix = "" if not current or current.endswith("\n\n") else (
                    "\n" if current.endswith("\n") else "\n\n"
                )
                self.editor.insert_at_cursor(f"{prefix}[{tag}]\n")
                self._mark_dirty()
                self.request_analysis(force=True)
                break
        self.section_menu.set(tr("sec.insert"))

    def set_status(self, message: str, kind: str = "info", busy: bool = False) -> None:
        colors = {
            "info": theme.default_text(), "ok": theme.color("good"),
            "warn": theme.color("warn"), "error": theme.color("bad"),
        }
        prefix = {"ok": "✓ ", "warn": "! ", "error": "✕ "}.get(kind, "")
        if busy:
            prefix = "⏳ "
        self.status_label.configure(text=prefix + message,
                                    text_color=colors.get(kind, theme.default_text()))

        if self._status_job is not None:
            try:
                self.after_cancel(self._status_job)
            except Exception:
                pass
            self._status_job = None
        if kind in {"ok", "warn"} and not busy:
            self._status_job = self.after(6000, lambda: self.set_status(tr("app.ready")))

    def on_close(self) -> None:
        if self._dirty and not messagebox.askyesno(
            tr("msg.question"), tr("msg.confirm_exit"), parent=self
        ):
            return
        try:
            self.config_store.set("window_geometry", self.winfo_geometry())
        except tk.TclError:
            pass
        self._snapshot_now(tr("hist.auto"))
        self.config_store.save()
        self.history.close()
        self.destroy()
