"""Okno ustawien: silniki AI, edytor, katalog danych."""

from __future__ import annotations

import os
import subprocess
import threading

import customtkinter as ctk

from ..ai.base import AIError
from ..ai.ollama import OllamaEngine
from ..ai.openrouter import OpenRouterEngine
from ..config import data_dir
from ..i18n import tr
from . import theme
from .widgets import Hint, SectionTitle

FONT_CHOICES = ["Consolas", "Cascadia Mono", "Courier New", "Segoe UI", "Georgia",
                "Times New Roman", "Verdana", "Arial"]


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.config_obj = app.settings

        self.title(tr("set.header"))
        self.geometry("620x680")
        self.minsize(560, 560)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        self.tab_ai = self.tabs.add(tr("set.ai"))
        self.tab_editor = self.tabs.add(tr("set.editor"))
        self.tab_general = self.tabs.add(tr("set.general"))

        self._build_ai_tab()
        self._build_editor_tab()
        self._build_general_tab()

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        buttons.grid_columnconfigure(0, weight=1)
        self.status = ctk.CTkLabel(buttons, text="", anchor="w",
                                   font=theme.font(size=11))
        self.status.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(buttons, text=tr("set.cancel"), width=100, fg_color="transparent",
                      border_width=1, text_color=theme.GHOST_TEXT, command=self.destroy).grid(row=0, column=1, padx=(0, 6))
        ctk.CTkButton(buttons, text=tr("set.save"), width=120,
                      command=self.save).grid(row=0, column=2)

        self.after(120, self.lift)

    # -- zakladka AI ------------------------------------------------------

    def _build_ai_tab(self) -> None:
        tab = self.tab_ai
        tab.grid_columnconfigure(0, weight=1)
        row = 0

        SectionTitle(tab, text="OpenRouter").grid(row=row, column=0, sticky="ew", pady=(6, 4))
        row += 1

        ctk.CTkLabel(tab, text=tr("set.or_key"), anchor="w",
                     font=theme.font(size=12)).grid(row=row, column=0, sticky="w")
        row += 1
        self.or_key = ctk.CTkEntry(tab, show="•", placeholder_text="sk-or-v1-...")
        self.or_key.insert(0, self.config_obj.get("openrouter_api_key", ""))
        self.or_key.grid(row=row, column=0, sticky="ew", pady=(2, 2))
        row += 1

        key_actions = ctk.CTkFrame(tab, fg_color="transparent")
        key_actions.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(key_actions, text="👁", variable=self.show_key_var, width=40,
                        command=self._toggle_key).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(key_actions, text=tr("set.test"), width=140,
                      command=lambda: self._test("openrouter")).grid(row=0, column=1)

        Hint(tab, text=tr("set.or_key_hint")).grid(row=row, column=0, sticky="ew", pady=(0, 8))
        row += 1

        ctk.CTkLabel(tab, text=tr("set.or_model"), anchor="w",
                     font=theme.font(size=12)).grid(row=row, column=0, sticky="w")
        row += 1
        self.or_model = ctk.CTkEntry(tab)
        self.or_model.insert(0, self.config_obj.get("openrouter_model", ""))
        self.or_model.grid(row=row, column=0, sticky="ew", pady=(2, 14))
        row += 1

        SectionTitle(tab, text="Ollama").grid(row=row, column=0, sticky="ew", pady=(6, 4))
        row += 1

        ctk.CTkLabel(tab, text=tr("set.ollama_url"), anchor="w",
                     font=theme.font(size=12)).grid(row=row, column=0, sticky="w")
        row += 1
        self.ollama_url = ctk.CTkEntry(tab, placeholder_text="http://localhost:11434")
        self.ollama_url.insert(0, self.config_obj.get("ollama_url", ""))
        self.ollama_url.grid(row=row, column=0, sticky="ew", pady=(2, 4))
        row += 1

        ctk.CTkButton(tab, text=tr("set.test"), width=140,
                      command=lambda: self._test("ollama")).grid(row=row, column=0,
                                                                 sticky="w", pady=(0, 8))
        row += 1

        ctk.CTkLabel(tab, text=tr("set.ollama_model"), anchor="w",
                     font=theme.font(size=12)).grid(row=row, column=0, sticky="w")
        row += 1
        self.ollama_model = ctk.CTkEntry(tab, placeholder_text="llama3.1")
        self.ollama_model.insert(0, self.config_obj.get("ollama_model", ""))
        self.ollama_model.grid(row=row, column=0, sticky="ew", pady=(2, 8))
        row += 1

        Hint(tab, text="ollama pull llama3.1  ·  ollama pull qwen2.5  ·  ollama serve").grid(
            row=row, column=0, sticky="ew"
        )

    def _toggle_key(self) -> None:
        self.or_key.configure(show="" if self.show_key_var.get() else "•")

    def _test(self, which: str) -> None:
        self.status.configure(text="...", text_color=theme.color("muted"))

        if which == "openrouter":
            engine = OpenRouterEngine(self.or_key.get().strip())
        else:
            engine = OllamaEngine(self.ollama_url.get().strip())

        def work() -> None:
            try:
                engine.test_connection()
                self.after(0, lambda: self.status.configure(
                    text=tr("set.test_ok"), text_color=theme.color("good")))
            except AIError as exc:
                msg = str(exc)
                if msg == "MISSING_KEY":
                    msg = tr("ai.no_key")
                elif msg == "NO_CONNECTION":
                    msg = tr("ai.no_ollama")
                self.after(0, lambda m=msg: self.status.configure(
                    text=tr("set.test_fail", err=m), text_color=theme.color("bad")))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda e=exc: self.status.configure(
                    text=tr("set.test_fail", err=e), text_color=theme.color("bad")))

        threading.Thread(target=work, daemon=True).start()

    # -- zakladka edytora -------------------------------------------------

    def _build_editor_tab(self) -> None:
        tab = self.tab_editor
        tab.grid_columnconfigure(0, weight=1)
        row = 0

        ctk.CTkLabel(tab, text=tr("set.font_family"), anchor="w",
                     font=theme.font(size=12)).grid(row=row, column=0, sticky="w", pady=(8, 0))
        row += 1
        self.font_family = ctk.CTkOptionMenu(tab, values=FONT_CHOICES)
        current_family = self.config_obj.get("editor_font_family", "Consolas")
        self.font_family.set(current_family if current_family in FONT_CHOICES
                             else FONT_CHOICES[0])
        self.font_family.grid(row=row, column=0, sticky="ew", pady=(2, 10))
        row += 1

        ctk.CTkLabel(tab, text=tr("set.font_size"), anchor="w",
                     font=theme.font(size=12)).grid(row=row, column=0, sticky="w")
        row += 1
        self.font_size = ctk.CTkOptionMenu(
            tab, values=[str(s) for s in range(10, 25)]
        )
        self.font_size.set(str(self.config_obj.get("editor_font_size", 14)))
        self.font_size.grid(row=row, column=0, sticky="ew", pady=(2, 14))
        row += 1

        self.gutter_var = ctk.BooleanVar(
            value=bool(self.config_obj.get("show_syllable_gutter", True))
        )
        ctk.CTkCheckBox(tab, text=tr("set.show_syllables"),
                        variable=self.gutter_var).grid(row=row, column=0, sticky="w", pady=4)
        row += 1

        self.live_var = ctk.BooleanVar(value=bool(self.config_obj.get("live_analysis", True)))
        ctk.CTkCheckBox(tab, text=tr("set.live_analysis"),
                        variable=self.live_var).grid(row=row, column=0, sticky="w", pady=4)
        row += 1

        self.rhyme_var = ctk.BooleanVar(
            value=bool(self.config_obj.get("highlight_rhymes", True))
        )
        ctk.CTkCheckBox(tab, text=tr("rhy.highlight"),
                        variable=self.rhyme_var).grid(row=row, column=0, sticky="w", pady=4)

    # -- zakladka ogolna --------------------------------------------------

    def _build_general_tab(self) -> None:
        tab = self.tab_general
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text=tr("hist.autosave_every"), anchor="w",
                     font=theme.font(size=12)).grid(row=0, column=0, sticky="w", pady=(8, 0))
        self.autosave = ctk.CTkOptionMenu(tab, values=["0", "1", "3", "5", "10", "15"])
        self.autosave.set(str(self.config_obj.get("history_autosave_minutes", 5)))
        self.autosave.grid(row=1, column=0, sticky="ew", pady=(2, 14))

        ctk.CTkLabel(tab, text=tr("set.storage"), anchor="w",
                     font=theme.font(size=12)).grid(row=2, column=0, sticky="w")
        path_label = ctk.CTkLabel(tab, text=str(data_dir()), anchor="w", justify="left",
                                  wraplength=520, text_color=theme.color("muted"),
                                  font=theme.font(size=11))
        path_label.grid(row=3, column=0, sticky="ew", pady=(2, 6))
        ctk.CTkButton(tab, text=tr("set.open_folder"), width=160,
                      command=self._open_folder).grid(row=4, column=0, sticky="w")

        Hint(tab, text="Lyrics Manager Pro").grid(row=5, column=0, sticky="ew", pady=(20, 0))

    def _open_folder(self) -> None:
        path = str(data_dir())
        try:
            if os.name == "nt":
                os.startfile(path)  # noqa: S606 - otwarcie wlasnego katalogu danych
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError:
            pass

    # -- zapis ------------------------------------------------------------

    def save(self) -> None:
        self.config_obj.update({
            "openrouter_api_key": self.or_key.get().strip(),
            "openrouter_model": self.or_model.get().strip(),
            "ollama_url": self.ollama_url.get().strip() or "http://localhost:11434",
            "ollama_model": self.ollama_model.get().strip(),
            "editor_font_family": self.font_family.get(),
            "editor_font_size": int(self.font_size.get()),
            "show_syllable_gutter": self.gutter_var.get(),
            "live_analysis": self.live_var.get(),
            "highlight_rhymes": self.rhyme_var.get(),
            "history_autosave_minutes": int(self.autosave.get()),
        })
        self.config_obj.save()
        self.app.apply_settings()
        self.destroy()
