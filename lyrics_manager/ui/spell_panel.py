"""Panel pisowni: stan slownika, lista bledow i zarzadzanie slownikami."""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ..i18n import tr
from ..spelling import (
    CATALOG, MANUAL_LINKS, SpellChecker, dictionaries_dir, download_dictionary,
    find_system_dictionaries, import_archive, import_system_dictionary,
    installed_codes, remove_dictionary, source_for,
)
from . import theme
from .widgets import Hint, ScrollList, SectionTitle, StatGrid


class SpellPanel(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._busy = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        row = 0
        self.title = SectionTitle(self, text=tr("sp.header"))
        self.title.grid(row=row, column=0, sticky="ew", pady=(4, 8))
        row += 1

        self.enabled_var = ctk.BooleanVar(
            value=bool(app.settings.get("spell_check_enabled", True))
        )
        self.enabled_cb = ctk.CTkCheckBox(
            self, text=tr("sp.enabled"), variable=self.enabled_var,
            command=self._toggle_enabled, font=theme.font(size=12),
        )
        self.enabled_cb.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1

        dict_row = ctk.CTkFrame(self, fg_color="transparent")
        dict_row.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        dict_row.grid_columnconfigure(1, weight=1)
        row += 1
        self.dict_label = ctk.CTkLabel(dict_row, text=tr("sp.dictionary"), anchor="w",
                                       font=theme.font(size=12))
        self.dict_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.dict_var = ctk.StringVar(value="—")
        self.dict_menu = ctk.CTkOptionMenu(dict_row, values=["—"], variable=self.dict_var,
                                           command=self._on_dict_change,
                                           dynamic_resizing=False)
        self.dict_menu.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.recheck_btn = ctk.CTkButton(dict_row, text="⟳", width=36,
                                         command=lambda: self.app.request_spellcheck(force=True))
        self.recheck_btn.grid(row=0, column=2)

        self.stats = StatGrid(self, columns=2)
        self.stats.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        row += 1

        self.status_note = ctk.CTkLabel(self, text="", anchor="w", justify="left",
                                        wraplength=380, font=theme.font(size=11))
        self.status_note.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        row += 1

        self.hint = Hint(self, text=tr("sp.hint"))
        self.hint.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        row += 1

        self.list = ScrollList(self, empty_text=tr("sp.no_errors"))
        self.list.grid(row=row, column=0, sticky="nsew", pady=(0, 8))
        row += 1

        self.manage_btn = ctk.CTkButton(
            self, text=f"{tr('sp.manage')} …", command=self.open_manager,
            fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
        )
        self.manage_btn.grid(row=row, column=0, sticky="ew")

        self.refresh_dictionary_list()
        self._poll_queue()

    # -- etykiety ---------------------------------------------------------

    def refresh_labels(self) -> None:
        self.title.configure(text=tr("sp.header"))
        self.enabled_cb.configure(text=tr("sp.enabled"))
        self.dict_label.configure(text=tr("sp.dictionary"))
        self.hint.configure(text=tr("sp.hint"))
        self.list.set_empty_text(tr("sp.no_errors"))
        self.manage_btn.configure(text=f"{tr('sp.manage')} …")
        self.refresh_dictionary_list()
        self.app.request_spellcheck(force=True)

    def refresh_theme(self) -> None:
        self.hint.refresh_theme()
        self.manage_btn.configure(text_color=theme.GHOST_TEXT)

    # -- ustawienia -------------------------------------------------------

    def _toggle_enabled(self) -> None:
        enabled = self.enabled_var.get()
        self.app.settings.set("spell_check_enabled", enabled)
        if enabled:
            self.app.request_spellcheck(force=True)
        else:
            self.app.editor.clear_spelling()
            self.update_report(None)

    def _on_dict_change(self, value: str) -> None:
        code = value.split(" ")[0]
        if not code or code == "—":
            return
        self.app.set_spell_dictionary(code)

    def refresh_dictionary_list(self) -> None:
        codes = installed_codes()
        values = codes or ["—"]
        self.dict_menu.configure(values=values)
        current = self.app.spell_code()
        self.dict_var.set(current if current in values else values[0])

    # -- raport -----------------------------------------------------------

    def update_report(self, report, state: str = "ready") -> None:
        """state: ready | loading | missing | off | no_engine"""
        labels = {
            "ready": tr("sp.status_ready"),
            "loading": tr("sp.status_loading"),
            "missing": tr("sp.status_missing"),
            "off": tr("sp.status_off"),
            "no_engine": tr("sp.status_missing"),
        }
        colors = {
            "ready": theme.color("good"), "loading": theme.color("warn"),
            "missing": theme.color("bad"), "off": theme.color("muted"),
            "no_engine": theme.color("bad"),
        }

        errors = report.error_count if report else 0
        checked = report.checked_words if report else 0
        accuracy = report.accuracy if report else 100.0

        self.stats.set_items([
            (tr("sp.status"), labels.get(state, state), colors.get(state)),
            (tr("sp.errors"), str(errors),
             theme.color("bad") if errors else theme.color("good")),
            (tr("sp.checked"), str(checked), None),
            (tr("sp.accuracy"), f"{accuracy:.1f}%", theme.score_color(accuracy)),
        ])

        note, note_color = "", theme.color("muted")
        if state == "no_engine":
            note, note_color = tr("sp.no_engine"), theme.color("bad")
        elif state == "missing":
            note, note_color = tr("sp.not_ready"), theme.color("warn")
        self.status_note.configure(text=note, text_color=note_color)

        self.list.clear()
        if not report or not report.unique:
            self.list.show_empty(
                tr("sp.no_errors") if state == "ready" else labels.get(state, "")
            )
            return

        first_line: dict[str, int] = {}
        for problem in report.problems:
            first_line.setdefault(problem.word, problem.line)

        for word, count in report.unique:
            lines = sorted({p.line for p in report.problems if p.word == word})
            self.list.add_row(
                word,
                f"{tr('rep.lines_col')}: {', '.join(str(n) for n in lines[:12])}",
                color=theme.color("bad"),
                badge=f"{count}×" if count > 1 else "",
                on_click=lambda n=first_line[word]: self.app.focus_line(n),
            )

    # -- okno zarzadzania slownikami --------------------------------------

    def open_manager(self) -> None:
        DictionaryManager(self.winfo_toplevel(), self.app, self)

    # -- kolejka watkow ---------------------------------------------------

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "status":
                    self.app.set_status(str(payload), kind="ok")
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)


class DictionaryManager(ctk.CTkToplevel):
    """Pobieranie, wgrywanie i usuwanie slownikow Hunspell."""

    def __init__(self, master, app, panel: SpellPanel):
        super().__init__(master)
        self.app = app
        self.panel = panel
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._downloading = False

        self.title(tr("sp.manage"))
        self.geometry("660x720")
        self.minsize(560, 560)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=0, column=0, sticky="nsew", padx=14, pady=(14, 6))
        body.grid_columnconfigure(0, weight=1)
        self.body = body

        row = 0
        Hint(body, text=tr("sp.links_hint"), wraplength=580).grid(
            row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # --- zainstalowane
        SectionTitle(body, text=tr("sp.installed")).grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.installed_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.installed_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        self.installed_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # --- do pobrania
        SectionTitle(body, text=tr("sp.available")).grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        self.available_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.available_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        self.available_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # --- inne zrodla
        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        row += 1
        ctk.CTkButton(actions, text=tr("sp.import_file"), command=self.import_file,
                      fg_color="transparent", border_width=1,
                      text_color=theme.GHOST_TEXT).grid(row=0, column=0, sticky="ew",
                                                        padx=(0, 4), pady=2)
        ctk.CTkButton(actions, text=tr("sp.scan_system"), command=self.scan_system,
                      fg_color="transparent", border_width=1,
                      text_color=theme.GHOST_TEXT).grid(row=0, column=1, sticky="ew",
                                                        padx=(4, 0), pady=2)
        ctk.CTkButton(actions, text=tr("sp.open_folder"), command=self.open_folder,
                      fg_color="transparent", border_width=1,
                      text_color=theme.GHOST_TEXT).grid(row=1, column=0, columnspan=2,
                                                        sticky="ew", pady=2)

        # --- linki
        SectionTitle(body, text=tr("sp.links")).grid(
            row=row, column=0, sticky="ew", pady=(0, 4))
        row += 1
        links = ctk.CTkFrame(body, fg_color="transparent")
        links.grid(row=row, column=0, sticky="ew")
        links.grid_columnconfigure(0, weight=1)
        for i, (label, url) in enumerate(MANUAL_LINKS):
            link = ctk.CTkLabel(links, text=f"🔗  {label}", anchor="w", justify="left",
                                cursor="hand2", wraplength=560,
                                text_color=theme.color("accent"),
                                font=theme.font(size=12, underline=True))
            link.grid(row=i * 2, column=0, sticky="ew", pady=(4, 0))
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            addr = ctk.CTkLabel(links, text=url, anchor="w", justify="left",
                                wraplength=560, text_color=theme.color("muted"),
                                font=theme.font(size=10))
            addr.grid(row=i * 2 + 1, column=0, sticky="ew")

        # --- stopka
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(footer, height=6)
        self.progress.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.progress.set(0)
        self.progress.grid_remove()
        self.status = ctk.CTkLabel(footer, text="", anchor="w", justify="left",
                                   wraplength=460, font=theme.font(size=11))
        self.status.grid(row=1, column=0, sticky="ew")
        ctk.CTkButton(footer, text=tr("set.close"), width=110,
                      command=self.destroy).grid(row=1, column=1, sticky="e")

        self.rebuild_lists()
        self._poll_queue()
        self.after(120, self.lift)

    # -- listy ------------------------------------------------------------

    def rebuild_lists(self) -> None:
        for frame in (self.installed_frame, self.available_frame):
            for child in frame.winfo_children():
                child.destroy()

        codes = installed_codes()

        if not codes:
            ctk.CTkLabel(self.installed_frame, text="—", anchor="w",
                         text_color=theme.color("muted"),
                         font=theme.font(size=12)).grid(row=0, column=0, sticky="w")
        for i, code in enumerate(codes):
            src = source_for(code)
            label = src.label if src else code
            size_mb = self._dictionary_size(code)
            card = ctk.CTkFrame(self.installed_frame, fg_color=("gray92", "gray17"),
                                corner_radius=6)
            card.grid(row=i, column=0, sticky="ew", pady=2)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=f"✓  {label}", anchor="w",
                         text_color=theme.color("good"),
                         font=theme.font(size=12, weight="bold")).grid(
                row=0, column=0, sticky="ew", padx=10, pady=(6, 0))
            ctk.CTkLabel(card, text=f"{tr('sp.size')}: {size_mb:.1f} MB", anchor="w",
                         text_color=theme.color("muted"),
                         font=theme.font(size=11)).grid(
                row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
            ctk.CTkButton(card, text=tr("sp.remove"), width=90, height=26,
                          fg_color="transparent", border_width=1,
                          text_color=theme.GHOST_TEXT,
                          command=lambda c=code: self.remove(c)).grid(
                row=0, column=1, rowspan=2, padx=10, pady=6)

        available = [s for s in CATALOG if s.code not in codes]
        if not available:
            ctk.CTkLabel(self.available_frame, text="—", anchor="w",
                         text_color=theme.color("muted"),
                         font=theme.font(size=12)).grid(row=0, column=0, sticky="w")
        for i, src in enumerate(available):
            card = ctk.CTkFrame(self.available_frame, fg_color=("gray92", "gray17"),
                                corner_radius=6)
            card.grid(row=i, column=0, sticky="ew", pady=2)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=src.label, anchor="w",
                         font=theme.font(size=12, weight="bold")).grid(
                row=0, column=0, sticky="ew", padx=10, pady=(6, 0))
            ctk.CTkLabel(
                card,
                text=f"{tr('sp.size')}: ~{src.approx_mb:.1f} MB · "
                     f"{tr('sp.license')}: {src.license}",
                anchor="w", justify="left", wraplength=380,
                text_color=theme.color("muted"), font=theme.font(size=11),
            ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
            ctk.CTkButton(card, text=tr("sp.download"), width=110, height=26,
                          command=lambda s=src: self.download(s)).grid(
                row=0, column=1, rowspan=2, padx=10, pady=6)

    @staticmethod
    def _dictionary_size(code: str) -> float:
        base = dictionaries_dir()
        total = 0
        for suffix in (".dic", ".aff"):
            path = base / f"{code}{suffix}"
            if path.exists():
                total += path.stat().st_size
        return total / (1024 * 1024)

    # -- akcje ------------------------------------------------------------

    def download(self, source) -> None:
        if self._downloading:
            return
        self._downloading = True
        self.progress.grid()
        self.progress.set(0)
        self.status.configure(
            text=tr("sp.downloading", name=source.label, pct=0),
            text_color=theme.color("muted"),
        )

        def on_progress(done: int, total: int) -> None:
            self._queue.put(("progress", (source.label, done, total)))

        def work() -> None:
            try:
                download_dictionary(source, progress=on_progress)
                self._queue.put(("done", source))
            except Exception as exc:  # noqa: BLE001 - komunikat trafia do okna
                self._queue.put(("error", exc))

        threading.Thread(target=work, daemon=True).start()

    def remove(self, code: str) -> None:
        src = source_for(code)
        name = src.label if src else code
        if not messagebox.askyesno(tr("msg.question"),
                                   tr("sp.confirm_remove", name=name), parent=self):
            return
        self.app.release_spell_dictionary(code)
        remove_dictionary(code)
        self.rebuild_lists()
        self.panel.refresh_dictionary_list()
        self.app.reload_spell_dictionary()

    def import_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self, title=tr("sp.import_file"),
            filetypes=[("LibreOffice / Hunspell", "*.oxt *.zip *.dic"),
                       ("All files", "*.*")],
        )
        if not path:
            return
        try:
            source = Path(path)
            if source.suffix.lower() in {".oxt", ".zip"}:
                installed = import_archive(source)
            else:
                installed = [import_system_dictionary(source)]
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(tr("msg.error"), tr("sp.import_failed", err=exc),
                                 parent=self)
            return
        if not installed:
            messagebox.showerror(tr("msg.error"),
                                 tr("sp.import_failed", err=".dic + .aff"), parent=self)
            return
        self._after_install(", ".join(installed), tr("sp.imported", name=", ".join(installed)))

    def scan_system(self) -> None:
        found = find_system_dictionaries()
        if not found:
            self.status.configure(text=tr("sp.scan_none"), text_color=theme.color("warn"))
            return
        installed = []
        for code, dic_path in found.items():
            try:
                installed.append(import_system_dictionary(dic_path))
            except Exception:  # noqa: BLE001 - pomijamy uszkodzone pary plikow
                continue
        if not installed:
            self.status.configure(text=tr("sp.scan_none"), text_color=theme.color("warn"))
            return
        self._after_install(", ".join(installed),
                            tr("sp.scan_found", name=", ".join(installed)))

    def _after_install(self, codes: str, message: str) -> None:
        self.rebuild_lists()
        self.panel.refresh_dictionary_list()
        self.app.reload_spell_dictionary()
        self.status.configure(text=message, text_color=theme.color("good"))

    def open_folder(self) -> None:
        path = str(dictionaries_dir())
        try:
            if os.name == "nt":
                os.startfile(path)  # noqa: S606 - wlasny katalog danych aplikacji
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError:
            pass

    # -- kolejka ----------------------------------------------------------

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "progress":
                    label, done, total = payload
                    fraction = min(1.0, done / max(1, total))
                    self.progress.set(fraction)
                    self.status.configure(
                        text=tr("sp.downloading", name=label, pct=int(fraction * 100)))
                elif kind == "done":
                    self._downloading = False
                    self.progress.set(1.0)
                    self.progress.grid_remove()
                    self.rebuild_lists()
                    self.panel.refresh_dictionary_list()
                    self.app.reload_spell_dictionary()
                    self.status.configure(text=tr("sp.downloaded", name=payload.label),
                                          text_color=theme.color("good"))
                elif kind == "error":
                    self._downloading = False
                    self.progress.grid_remove()
                    self.status.configure(text=tr("sp.download_failed", err=payload),
                                          text_color=theme.color("bad"))
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(120, self._poll_queue)
