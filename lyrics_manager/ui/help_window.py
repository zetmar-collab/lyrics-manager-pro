"""Okno instrukcji obslugi (PL / EN) z lista sekcji i tabela skrotow."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox

import customtkinter as ctk

from ..help_content import CONTENT, SECTION_KEYS
from ..i18n import get_ui_language, tr
from ..shortcuts import GROUPS, by_group
from . import theme


class HelpWindow(ctk.CTkToplevel):
    """Instrukcja obslugi. Tresc zmienia sie razem z jezykiem interfejsu."""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._current = SECTION_KEYS[0]
        self._buttons: dict[str, ctk.CTkButton] = {}

        self.title(tr("help.title"))
        self._apply_geometry()
        self.transient(master)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- lista sekcji
        sidebar = ctk.CTkScrollableFrame(self, width=220, fg_color="transparent")
        sidebar.grid(row=0, column=0, sticky="nsw", padx=(12, 6), pady=12)
        sidebar.grid_columnconfigure(0, weight=1)
        for i, key in enumerate(SECTION_KEYS):
            button = ctk.CTkButton(
                sidebar, text=tr(f"help.sec.{key}"), height=30, anchor="w",
                corner_radius=6, border_width=1, border_color=("gray75", "gray30"),
                font=theme.font(size=12), command=lambda k=key: self.show(k),
            )
            button.grid(row=i, column=0, sticky="ew", pady=2)
            self._buttons[key] = button

        # --- tresc
        body = ctk.CTkFrame(self)
        body.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._base_size = 12
        self._font = tkfont.Font(family="Segoe UI", size=self._base_size)
        self._h1 = tkfont.Font(family="Segoe UI", size=self._base_size + 7, weight="bold")
        self._h2 = tkfont.Font(family="Segoe UI", size=self._base_size + 2, weight="bold")
        self._mono = tkfont.Font(family="Consolas", size=self._base_size - 1)
        self._bold = tkfont.Font(family="Segoe UI", size=self._base_size, weight="bold")

        self.text = tk.Text(
            body, wrap="word", borderwidth=0, highlightthickness=0,
            padx=22, pady=16, font=self._font, state="disabled", cursor="arrow",
            spacing1=2, spacing3=4, height=10, width=40,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ctk.CTkScrollbar(body, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.bind("<MouseWheel>",
                       lambda e: (self.text.yview_scroll(-1 * (e.delta // 120), "units"),
                                  "break")[1])

        # --- stopka
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        footer.grid_columnconfigure(0, weight=1)
        self.hint = ctk.CTkLabel(footer, text=tr("help.hint"), anchor="w",
                                 text_color=theme.color("muted"), font=theme.font(size=11))
        self.hint.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(footer, text=tr("help.save"), width=150, fg_color="transparent",
                      border_width=1, text_color=theme.GHOST_TEXT,
                      command=self.save_to_file).grid(row=0, column=1, padx=(0, 6))
        ctk.CTkButton(footer, text=tr("set.close"), width=110,
                      command=self.destroy).grid(row=0, column=2)

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F1>", lambda e: self.destroy())
        self.bind("<Prior>", lambda e: self._step(-1))
        self.bind("<Next>", lambda e: self._step(1))

        self.refresh_theme()
        self.show(self._current)
        self.after(150, self.lift)

    # -- ustawienia okna --------------------------------------------------

    def _apply_geometry(self) -> None:
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        width = min(1040, max(760, screen_w - 200))
        height = min(760, max(560, screen_h - 160))
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height - 60) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(720, 520)

    def _step(self, delta: int) -> None:
        index = SECTION_KEYS.index(self._current)
        self.show(SECTION_KEYS[(index + delta) % len(SECTION_KEYS)])

    # -- renderowanie -----------------------------------------------------

    def show(self, key: str) -> None:
        self._current = key
        for name, button in self._buttons.items():
            if name == key:
                button.configure(fg_color=("#BFDBFE", "#1D4ED8"),
                                 text_color=("gray10", "#FFFFFF"))
            else:
                button.configure(fg_color="transparent",
                                 text_color=("gray20", "gray85"))

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        if key == "shortcuts":
            self._render_shortcuts()
        else:
            body = CONTENT.get(key, {}).get(get_ui_language(), "")
            self._render_markup(body)
        self.text.configure(state="disabled")
        self.text.yview_moveto(0)

    def _render_markup(self, raw: str) -> None:
        """Renderuje tresc, sklejajac kolejne wiersze w akapity.

        Tekst zrodlowy jest lamany na 78 znakow dla czytelnosci w pliku, ale
        w oknie ma sie zawijac do jego szerokosci - dlatego akapit skladamy
        z powrotem w jedna calosc.
        """
        buffer: list[str] = []          # zbierany akapit
        buffer_kind = "body"            # "body" | "bullet" | "note"

        def flush() -> None:
            nonlocal buffer, buffer_kind
            if buffer:
                self._render_paragraph(" ".join(buffer), buffer_kind)
                buffer = []
                buffer_kind = "body"

        previous_was_heading = False

        for line in raw.strip("\n").splitlines():
            stripped = line.strip()
            indented = line.startswith("    ") or line.startswith("\t")

            if not stripped:
                flush()
                if not previous_was_heading:
                    self.text.insert("end", "\n")
                continue

            if stripped.startswith("# "):
                flush()
                self.text.insert("end", stripped[2:] + "\n", "h1")
                previous_was_heading = True
                continue
            if stripped.startswith("## "):
                flush()
                self.text.insert("end", stripped[3:] + "\n", "h2")
                previous_was_heading = True
                continue

            previous_was_heading = False

            if stripped.startswith("|"):
                flush()
                self._render_table_row(stripped)
            elif indented and not stripped.startswith("- "):
                flush()
                self.text.insert("end", stripped + "\n", "code")
            elif stripped.startswith("- "):
                flush()
                buffer = ["•  " + stripped[2:]]
                buffer_kind = "bullet"
            elif stripped.startswith("> "):
                flush()
                buffer = [stripped[2:]]
                buffer_kind = "note"
            elif buffer:
                buffer.append(stripped)      # ciag dalszy akapitu lub punktu
            else:
                buffer = [stripped]
                buffer_kind = "body"

        flush()

    def _render_paragraph(self, text: str, kind: str) -> None:
        """Wstawia akapit i nadaje mu wciecia na calej dlugosci.

        Znacznik akapitu trzeba nalozyc po wstawieniu, bo fragmenty pogrubione
        maja wlasny znacznik i inaczej zawiniete wiersze gubilyby wciecie.
        """
        start = self.text.index("end-1c")
        self._render_inline(text + "\n", kind)
        self.text.tag_add(kind, start, "end-1c")

    def _render_table_row(self, line: str) -> None:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):   # linia oddzielajaca naglowek
            return
        rendered = "   ".join(f"{c}" for c in cells)
        self._render_inline("   " + rendered + "\n", "body")

    def _render_inline(self, text: str, tag: str) -> None:
        """Obsluguje **pogrubienie** i `kod` wewnatrz wiersza."""
        rest = text
        while rest:
            bold_at = rest.find("**")
            code_at = rest.find("`")
            candidates = [p for p in (bold_at, code_at) if p >= 0]
            if not candidates:
                self.text.insert("end", rest, tag)
                return
            first = min(candidates)
            if first > 0:
                self.text.insert("end", rest[:first], tag)
                rest = rest[first:]
                continue
            if rest.startswith("**"):
                end = rest.find("**", 2)
                if end < 0:
                    self.text.insert("end", rest, tag)
                    return
                self.text.insert("end", rest[2:end], "strong")
                rest = rest[end + 2:]
            else:
                end = rest.find("`", 1)
                if end < 0:
                    self.text.insert("end", rest, tag)
                    return
                self.text.insert("end", rest[1:end], "code_inline")
                rest = rest[end + 1:]

    def _render_shortcuts(self) -> None:
        self.text.insert("end", tr("help.sec.shortcuts") + "\n\n", "h1")
        self._render_inline(tr("help.shortcuts_intro") + "\n", "body")
        for group in GROUPS:
            entries = by_group(group)
            if not entries:
                continue
            self.text.insert("end", "\n" + tr(f"key.group.{group}") + "\n", "h2")
            width = max(len(s.label) for s in entries) + 3
            for shortcut in entries:
                self.text.insert("end", f"{shortcut.label:<{width}}", "kbd")
                suffix = "  " + tr("help.native") if shortcut.native else ""
                self.text.insert("end", tr(f"key.{shortcut.action}") + suffix + "\n",
                                 "body")

    # -- eksport ----------------------------------------------------------

    def as_markdown(self) -> str:
        lang = get_ui_language()
        parts = [f"# {tr('help.title')} — {tr('app.title')}", ""]
        for key in SECTION_KEYS:
            if key == "shortcuts":
                parts.append(f"## {tr('help.sec.shortcuts')}")
                parts.append("")
                for group in GROUPS:
                    entries = by_group(group)
                    if not entries:
                        continue
                    parts.append(f"### {tr(f'key.group.{group}')}")
                    parts.append("")
                    parts.append("| " + tr("help.col_key") + " | "
                                 + tr("help.col_action") + " |")
                    parts.append("|---|---|")
                    for shortcut in entries:
                        suffix = f" ({tr('help.native')})" if shortcut.native else ""
                        parts.append(f"| `{shortcut.label}` | "
                                     f"{tr(f'key.{shortcut.action}')}{suffix} |")
                    parts.append("")
                continue
            body = CONTENT.get(key, {}).get(lang, "").strip("\n")
            # naglowek "# " w tresci schodzi o poziom nizej w pliku
            body = "\n".join(
                ("#" + line) if line.startswith("# ") else line
                for line in body.splitlines()
            )
            parts.append(body)
            parts.append("")
        return "\n".join(parts)

    def save_to_file(self) -> None:
        suffix = "PL" if get_ui_language() == "pl" else "EN"
        path = filedialog.asksaveasfilename(
            parent=self, title=tr("help.save"), defaultextension=".md",
            initialfile=f"Lyrics_Manager_Pro_{suffix}.md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            Path(path).write_text(self.as_markdown(), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror(tr("msg.error"), tr("msg.save_failed", err=exc),
                                 parent=self)
            return
        self.app.set_status(tr("msg.file_saved", path=path), kind="ok")

    # -- wyglad -----------------------------------------------------------

    def refresh_theme(self) -> None:
        p = theme.palette()
        self.text.configure(
            background=p["editor_bg"], foreground=p["editor_fg"],
            selectbackground=p["editor_select_bg"], selectforeground=p["editor_select_fg"],
            insertbackground=p["editor_bg"],
        )
        self.text.tag_configure("h1", font=self._h1, foreground=p["accent"],
                                spacing1=2, spacing3=12)
        self.text.tag_configure("h2", font=self._h2, foreground=p["editor_fg"],
                                spacing1=10, spacing3=4)
        self.text.tag_configure("body", font=self._font, lmargin1=0, lmargin2=0)
        self.text.tag_configure("strong", font=self._bold)
        self.text.tag_configure("bullet", font=self._font, lmargin1=14, lmargin2=32)
        self.text.tag_configure("note", font=self._font, foreground=p["muted"],
                                lmargin1=14, lmargin2=14, spacing1=6, spacing3=6)
        self.text.tag_configure("code", font=self._mono, foreground=p["good"],
                                lmargin1=28, lmargin2=28)
        self.text.tag_configure("code_inline", font=self._mono, foreground=p["good"])
        self.text.tag_configure("kbd", font=self._mono, foreground=p["accent"],
                                lmargin1=14, lmargin2=14)

        # Znaczniki akapitu ("bullet", "note") obejmuja caly wiersz, wiec bez
        # tego nadpisalyby czcionke fragmentow pogrubionych i kodu w linii -
        # w Tk wygrywa znacznik o wyzszym priorytecie, a nie ten wezszy.
        self.text.tag_raise("strong")
        self.text.tag_raise("code_inline")

        self.hint.configure(text_color=theme.color("muted"))

    def refresh_labels(self) -> None:
        self.title(tr("help.title"))
        for key, button in self._buttons.items():
            button.configure(text=tr(f"help.sec.{key}"))
        self.hint.configure(text=tr("help.hint"))
        self.show(self._current)
