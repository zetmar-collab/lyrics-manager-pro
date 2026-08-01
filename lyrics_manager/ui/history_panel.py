"""Panel historii zmian - lista migawek, podglad, diff, przywracanie."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from ..history import Snapshot, changed_line_count, diff_text
from ..i18n import tr
from . import theme
from .editor import ReadOnlyText
from .widgets import ScrollList, SectionTitle


class HistoryPanel(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._snapshots: list[Snapshot] = []
        self._selected: Snapshot | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=2)
        self.grid_rowconfigure(5, weight=3)

        self.title = SectionTitle(self, text=tr("hist.header"))
        self.title.grid(row=0, column=0, sticky="ew", pady=(4, 8))

        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        save_frame.grid_columnconfigure(0, weight=1)
        self.label_entry = ctk.CTkEntry(save_frame, placeholder_text=tr("hist.label"))
        self.label_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.label_entry.bind("<Return>", lambda e: self.save_snapshot())
        self.save_btn = ctk.CTkButton(save_frame, text=tr("hist.snapshot"), width=150,
                                      command=self.save_snapshot)
        self.save_btn.grid(row=0, column=1)

        auto_frame = ctk.CTkFrame(self, fg_color="transparent")
        auto_frame.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        self.auto_label = ctk.CTkLabel(auto_frame, text=tr("hist.autosave_every"),
                                       font=theme.font(size=12), anchor="w")
        self.auto_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.auto_var = ctk.StringVar(
            value=str(app.settings.get("history_autosave_minutes", 5))
        )
        self.auto_menu = ctk.CTkOptionMenu(
            auto_frame, values=["0", "1", "3", "5", "10", "15"], variable=self.auto_var,
            width=80, command=self._on_auto_change,
        )
        self.auto_menu.grid(row=0, column=1, sticky="w")

        self.list = ScrollList(self, empty_text=tr("hist.empty"))
        self.list.grid(row=3, column=0, sticky="nsew", pady=(0, 6))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        for c in range(3):
            actions.grid_columnconfigure(c, weight=1)
        self.restore_btn = ctk.CTkButton(actions, text=tr("hist.restore"), height=28,
                                         command=self.restore, state="disabled",
                                         font=theme.font(size=11))
        self.restore_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.diff_btn = ctk.CTkButton(actions, text=tr("hist.diff"), height=28,
                                      fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
                                      command=self.show_diff, state="disabled",
                                      font=theme.font(size=11))
        self.diff_btn.grid(row=0, column=1, sticky="ew", padx=3)
        self.delete_btn = ctk.CTkButton(actions, text=tr("hist.delete"), height=28,
                                        fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
                                        command=self.delete, state="disabled",
                                        font=theme.font(size=11))
        self.delete_btn.grid(row=0, column=2, sticky="ew", padx=(3, 0))

        self.preview = ReadOnlyText(self, font_size=11)
        self.preview.grid(row=5, column=0, sticky="nsew")

    # -- etykiety ---------------------------------------------------------

    def refresh_labels(self) -> None:
        self.title.configure(text=tr("hist.header"))
        self.label_entry.configure(placeholder_text=tr("hist.label"))
        self.save_btn.configure(text=tr("hist.snapshot"))
        self.auto_label.configure(text=tr("hist.autosave_every"))
        self.restore_btn.configure(text=tr("hist.restore"))
        self.diff_btn.configure(text=tr("hist.diff"))
        self.delete_btn.configure(text=tr("hist.delete"))
        self.list.set_empty_text(tr("hist.empty"))
        self.reload()

    def refresh_theme(self) -> None:
        self.preview.refresh_theme()

    def _on_auto_change(self, value: str) -> None:
        try:
            self.app.settings.set("history_autosave_minutes", int(value))
        except ValueError:
            pass
        self.app.reschedule_autosave()

    # -- dane -------------------------------------------------------------

    def reload(self) -> None:
        self._snapshots = self.app.history.list(self.app.song_key())
        self.list.clear()
        if not self._snapshots:
            self.list.show_empty(tr("hist.empty"))
            self._set_actions(False)
            return

        for snap in self._snapshots:
            label = snap.label or tr(f"hist.{snap.kind}")
            color = theme.color("accent") if snap.kind == "manual" else None
            self.list.add_row(
                f"{snap.timestamp:%Y-%m-%d %H:%M}  ·  {label}",
                f"{snap.lines} {tr('rep.lines_col')} · {snap.words} "
                f"{tr('syl.words').lower()} · {snap.chars} {tr('exp.chars')}",
                color=color,
                badge=tr(f"hist.{snap.kind}"),
                on_click=lambda s=snap: self.select(s),
            )

    def select(self, snapshot: Snapshot) -> None:
        self._selected = snapshot
        self._set_actions(True)
        self.preview.set_content(snapshot.content)

    def _set_actions(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.restore_btn.configure(state=state)
        self.diff_btn.configure(state=state)
        self.delete_btn.configure(state=state)

    # -- akcje ------------------------------------------------------------

    def save_snapshot(self, label: str | None = None, kind: str = "manual") -> None:
        text = self.app.get_text()
        if not text.strip():
            return
        chosen = label if label is not None else self.label_entry.get().strip()
        snap = self.app.history.add(self.app.song_key(), text, chosen, kind)
        if snap:
            self.app.history.prune(self.app.song_key())
            self.label_entry.delete(0, "end")
            self.reload()

    def show_diff(self) -> None:
        if not self._selected:
            return
        current = self.app.get_text()
        diff = diff_text(
            self._selected.content, current,
            f"{self._selected.timestamp:%Y-%m-%d %H:%M}", tr("app.title"),
        )
        changed = changed_line_count(self._selected.content, current)
        if not diff.strip():
            self.preview.set_content(tr("hist.identical"))
            return
        self.preview.set_diff(
            f"# {changed} {tr('hist.words_changed')}\n\n{diff}"
        )

    def restore(self) -> None:
        if not self._selected:
            return
        if not messagebox.askyesno(tr("msg.question"), tr("hist.confirm_restore"),
                                   parent=self.winfo_toplevel()):
            return
        self.save_snapshot(label=tr("hist.auto"), kind="auto")
        self.app.set_text(self._selected.content)
        self.app.set_status(tr("hist.restored"), kind="ok")
        self.reload()

    def delete(self) -> None:
        if not self._selected:
            return
        if not messagebox.askyesno(tr("msg.question"), tr("hist.confirm_delete"),
                                   parent=self.winfo_toplevel()):
            return
        self.app.history.delete(self._selected.id)
        self._selected = None
        self.preview.clear()
        self._set_actions(False)
        self.reload()
