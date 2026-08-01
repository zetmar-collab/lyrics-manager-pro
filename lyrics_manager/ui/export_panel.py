"""Panel eksportu: Suno, Udio, czysty tekst, Markdown z analiza."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ..export import LIMITS, build_style_prompt, check_limit, export_text
from ..i18n import tr
from . import theme
from .editor import ReadOnlyText
from .widgets import SectionTitle, make_segmented

TARGETS = ["suno", "udio", "plain", "markdown"]
TARGET_KEYS = {"suno": "exp.suno", "udio": "exp.udio",
               "plain": "exp.plain", "markdown": "exp.markdown"}

EXTENSIONS = {"suno": ".txt", "udio": ".txt", "plain": ".txt", "markdown": ".md"}


class ExportPanel(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.title = SectionTitle(self, text=tr("exp.header"))
        self.title.grid(row=0, column=0, sticky="ew", pady=(4, 8))

        self.target_label = ctk.CTkLabel(self, text=tr("exp.target"), anchor="w",
                                         font=theme.font(size=12))
        self.target_label.grid(row=1, column=0, sticky="w")
        self.target_menu = make_segmented(
            self, values=self._target_values(), command=lambda _v: self.refresh_preview()
        )
        self.target_menu.grid(row=2, column=0, sticky="ew", pady=(2, 8))
        self.target_menu.set(tr("exp.suno"))

        opts = ctk.CTkFrame(self, fg_color="transparent")
        opts.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self.autotag_var = ctk.BooleanVar(value=bool(app.settings.get("export_autotag", True)))
        self.autotag_cb = ctk.CTkCheckBox(
            opts, text=tr("exp.autotag"), variable=self.autotag_var,
            command=self.refresh_preview, font=theme.font(size=12),
        )
        self.autotag_cb.grid(row=0, column=0, sticky="w", pady=2)
        self.meta_var = ctk.BooleanVar(value=bool(app.settings.get("export_include_meta", True)))
        self.meta_cb = ctk.CTkCheckBox(
            opts, text=tr("exp.include_meta"), variable=self.meta_var,
            command=self.refresh_preview, font=theme.font(size=12),
        )
        self.meta_cb.grid(row=1, column=0, sticky="w", pady=2)

        self.style_label = ctk.CTkLabel(self, text=tr("exp.style_prompt"), anchor="w",
                                        font=theme.font(size=12))
        self.style_label.grid(row=4, column=0, sticky="w")
        self.style_value = ctk.CTkLabel(self, text="", anchor="w", justify="left",
                                        wraplength=380, text_color=theme.color("muted"),
                                        font=theme.font(size=11))
        self.style_value.grid(row=5, column=0, sticky="ew", pady=(0, 6))

        self.preview = ReadOnlyText(self, font_size=12)
        self.preview.grid(row=6, column=0, sticky="nsew", pady=(0, 6))

        self.info = ctk.CTkLabel(self, text="", anchor="w", justify="left", wraplength=380,
                                 font=theme.font(size=11))
        self.info.grid(row=7, column=0, sticky="ew", pady=(0, 6))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=8, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        self.copy_btn = ctk.CTkButton(actions, text=tr("exp.copy"), command=self.copy)
        self.copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.save_btn = ctk.CTkButton(actions, text=tr("exp.save_file"), command=self.save,
                                      fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT)
        self.save_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    # -- etykiety ---------------------------------------------------------

    def _target_values(self) -> list[str]:
        return [tr(TARGET_KEYS[t]) for t in TARGETS]

    def current_target(self) -> str:
        label = self.target_menu.get()
        for target in TARGETS:
            if tr(TARGET_KEYS[target]) == label:
                return target
        return "suno"

    def refresh_labels(self) -> None:
        target = self.current_target()
        self.title.configure(text=tr("exp.header"))
        self.target_label.configure(text=tr("exp.target"))
        self.target_menu.configure(values=self._target_values())
        self.target_menu.set(tr(TARGET_KEYS[target]))
        self.autotag_cb.configure(text=tr("exp.autotag"))
        self.meta_cb.configure(text=tr("exp.include_meta"))
        self.style_label.configure(text=tr("exp.style_prompt"))
        self.copy_btn.configure(text=tr("exp.copy"))
        self.save_btn.configure(text=tr("exp.save_file"))
        self.refresh_preview()

    def refresh_theme(self) -> None:
        self.preview.refresh_theme()
        self.style_value.configure(text_color=theme.color("muted"))

    # -- podglad ----------------------------------------------------------

    def build_content(self) -> str:
        target = self.current_target()
        self.app.settings.set("export_autotag", self.autotag_var.get())
        self.app.settings.set("export_include_meta", self.meta_var.get())
        return export_text(
            target,
            self.app.get_text(),
            self.app.document.meta,
            autotag=self.autotag_var.get(),
            include_meta=self.meta_var.get(),
            text_lang=self.app.text_language(),
        )

    def refresh_preview(self) -> None:
        target = self.current_target()
        content = self.build_content()
        self.preview.set_content(content)

        style = build_style_prompt(self.app.document.meta, target)
        self.style_value.configure(text=style or "—")

        ok, limit = check_limit(target, content)
        length = len(content)
        if limit and not ok:
            self.info.configure(
                text=f"{length} {tr('exp.chars')} — "
                     + tr("exp.limit_warn", limit=limit, target=tr(TARGET_KEYS[target])),
                text_color=theme.color("bad"),
            )
        elif limit:
            self.info.configure(text=f"{length} / {limit} {tr('exp.chars')}",
                                text_color=theme.color("good"))
        else:
            self.info.configure(text=f"{length} {tr('exp.chars')}",
                                text_color=theme.color("muted"))

    # -- akcje ------------------------------------------------------------

    def copy(self) -> None:
        self.app.copy_to_clipboard(self.build_content())
        self.app.set_status(tr("exp.copied"), kind="ok")

    def save(self) -> None:
        target = self.current_target()
        ext = EXTENSIONS[target]
        base = self.app.document.display_title or tr("app.untitled")
        safe = "".join(ch for ch in base if ch not in '<>:"/\\|?*').strip() or "lyrics"
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title=tr("exp.save_file"),
            defaultextension=ext,
            initialfile=f"{safe}_{target}{ext}",
            initialdir=self.app.settings.get("last_directory") or None,
            filetypes=[("Text", "*.txt"), ("Markdown", "*.md"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            Path(path).write_text(self.build_content(), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror(tr("msg.error"), tr("msg.save_failed", err=exc),
                                 parent=self.winfo_toplevel())
            return
        self.app.settings.set("last_directory", str(Path(path).parent))
        self.app.set_status(tr("msg.file_saved", path=path), kind="ok")
