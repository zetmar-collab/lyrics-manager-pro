"""Panele analityczne: sylaby, rymy, powtorzenia, czytelnosc."""

from __future__ import annotations

import customtkinter as ctk

from ..analysis.readability import analyze_readability
from ..analysis.repetition import analyze_repetition
from ..analysis.rhymes import (
    QUALITY_ASSONANCE, QUALITY_IDENTITY, QUALITY_PERFECT, QUALITY_SLANT,
    analyze_rhymes, find_rhymes, words_from_text,
)
from ..analysis.syllables import analyze_syllables
from ..i18n import tr
from . import theme
from .widgets import Hint, MeterBar, ScrollList, SectionTitle, StatGrid

QUALITY_KEYS = {
    QUALITY_IDENTITY: "rhy.type_identity",
    QUALITY_PERFECT: "rhy.type_perfect",
    QUALITY_SLANT: "rhy.type_slant",
    QUALITY_ASSONANCE: "rhy.type_assonance",
}


class BasePanel(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.grid_columnconfigure(0, weight=1)

    # kazdy panel implementuje ponizsze
    def refresh_labels(self) -> None:  # pragma: no cover - UI
        pass

    def update_report(self, text: str, lang: str) -> None:  # pragma: no cover - UI
        pass

    def refresh_theme(self) -> None:  # pragma: no cover - UI
        pass


# --------------------------------------------------------------------------
# SYLABY
# --------------------------------------------------------------------------

class SyllablePanel(BasePanel):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_rowconfigure(4, weight=1)

        self.title = SectionTitle(self, text=tr("syl.header"))
        self.title.grid(row=0, column=0, sticky="ew", pady=(4, 8))

        self.stats = StatGrid(self, columns=2)
        self.stats.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.hint = Hint(self, text=tr("syl.hint"))
        self.hint.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self.dist_title = ctk.CTkLabel(self, text=tr("syl.per_line"), anchor="w",
                                       font=theme.font(size=12, weight="bold"))
        self.dist_title.grid(row=3, column=0, sticky="ew")

        self.list = ScrollList(self)
        self.list.grid(row=4, column=0, sticky="nsew", pady=(4, 0))

    def refresh_labels(self) -> None:
        self.title.configure(text=tr("syl.header"))
        self.hint.configure(text=tr("syl.hint"))
        self.dist_title.configure(text=tr("syl.per_line"))

    def refresh_theme(self) -> None:
        self.hint.refresh_theme()

    def update_report(self, text: str, lang: str) -> None:
        report = analyze_syllables(text, lang)
        self.stats.set_items([
            (tr("syl.total_lines"), str(report.total_lines), None),
            (tr("syl.total_syllables"), str(report.total_syllables), None),
            (tr("syl.avg"), f"{report.average:.1f}", None),
            (tr("syl.min_max"), f"{report.minimum} / {report.maximum}", None),
            (tr("syl.words"), str(report.total_words), None),
            (tr("syl.variance"), f"{report.evenness:.0f}%",
             theme.score_color(report.evenness)),
        ])

        self.list.clear()
        if not report.histogram:
            self.list.show_empty(tr("list.empty"))
            return

        peak = max(count for _, count in report.histogram)
        for syllables, count in report.histogram:
            bar = "█" * max(1, round(14 * count / peak))
            self.list.add_row(
                f"{syllables:>2} {tr('syl.unit')}   {bar}",
                badge=f"{count}×",
            )
        if report.sections:
            for section in report.sections:
                if not section.lines:
                    continue
                avg = section.syllables / section.lines
                self.list.add_row(
                    f"[{section.name}]",
                    f"{section.lines} × {tr('syl.total_lines').lower()} · "
                    f"{tr('syl.avg').lower()} {avg:.1f}",
                    color=theme.color("section_fg"),
                    on_click=lambda n=section.start_line: self.app.focus_line(n),
                )


# --------------------------------------------------------------------------
# RYMY
# --------------------------------------------------------------------------

class RhymePanel(BasePanel):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_rowconfigure(6, weight=1)
        self._lang = "pl"

        self.title = SectionTitle(self, text=tr("rhy.header"))
        self.title.grid(row=0, column=0, sticky="ew", pady=(4, 8))

        self.stats = StatGrid(self, columns=2)
        self.stats.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        self.scheme_label = ctk.CTkLabel(
            self, text="", anchor="w", justify="left", wraplength=380,
            font=theme.font(family="Consolas", size=13, weight="bold"),
        )
        self.scheme_label.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        self.highlight_var = ctk.BooleanVar(value=True)
        self.highlight_cb = ctk.CTkCheckBox(
            self, text=tr("rhy.highlight"), variable=self.highlight_var,
            command=self._toggle_highlight, font=theme.font(size=12),
        )
        self.highlight_cb.grid(row=3, column=0, sticky="w", pady=(0, 8))

        finder = ctk.CTkFrame(self, fg_color="transparent")
        finder.grid(row=4, column=0, sticky="ew", pady=(0, 4))
        finder.grid_columnconfigure(0, weight=1)
        self.find_entry = ctk.CTkEntry(finder, placeholder_text=tr("rhy.find_for"))
        self.find_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.find_entry.bind("<Return>", lambda e: self.find_rhymes())
        self.find_btn = ctk.CTkButton(finder, text=tr("rhy.find_btn"), width=80,
                                      command=self.find_rhymes)
        self.find_btn.grid(row=0, column=1)

        self.ai_btn = ctk.CTkButton(
            self, text=tr("rhy.ai_suggest"), fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
            command=self._ask_ai, font=theme.font(size=12),
        )
        self.ai_btn.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        self.list = ScrollList(self)
        self.list.grid(row=6, column=0, sticky="nsew")

    def refresh_labels(self) -> None:
        self.title.configure(text=tr("rhy.header"))
        self.highlight_cb.configure(text=tr("rhy.highlight"))
        self.find_entry.configure(placeholder_text=tr("rhy.find_for"))
        self.find_btn.configure(text=tr("rhy.find_btn"))
        self.ai_btn.configure(text=tr("rhy.ai_suggest"))

    def _toggle_highlight(self) -> None:
        self.app.set_rhyme_highlight(self.highlight_var.get())

    def _ask_ai(self) -> None:
        word = self.find_entry.get().strip()
        self.app.request_ai_rhymes(word)

    def update_report(self, text: str, lang: str) -> None:
        self._lang = lang
        report = analyze_rhymes(text, lang)
        self.app.last_rhyme_report = report

        self.stats.set_items([
            (tr("rhy.density"), f"{report.density:.0f}%",
             theme.score_color(report.density)),
            (tr("rhy.perfect"), str(report.perfect_count), theme.color("good")),
            (tr("rhy.slant"), str(report.slant_count), theme.color("warn")),
            (tr("rhy.none"), str(len(report.unrhymed)),
             theme.color("bad") if report.unrhymed else theme.color("good")),
            (tr("rhy.internal"), str(len(report.internal)), None),
            (tr("rhy.groups"), str(len(report.groups)), None),
        ])

        scheme = report.scheme or "—"
        self.scheme_label.configure(text=f"{tr('rhy.scheme')}:  {scheme}")

        self.list.clear()
        if not report.groups and not report.internal:
            self.list.show_empty(tr("rhy.no_rhymes"))
            return

        letters: dict[str, int] = {}
        for group in report.groups:
            if group.letter not in letters:
                letters[group.letter] = len(letters)
            color = theme.rhyme_color(letters[group.letter])
            quality = tr(QUALITY_KEYS.get(group.quality, "rhy.type_slant"))
            lines = ", ".join(str(n) for n in group.lines)
            self.list.add_row(
                f"{group.letter}   {' · '.join(group.words)}",
                f"{quality} · {tr('rep.lines_col')}: {lines}",
                color=color,
                on_click=lambda n=group.lines[0]: self.app.focus_line(n),
                badge=f"{len(group.lines)}×",
            )

        for internal in report.internal[:20]:
            self.list.add_row(
                f"↔ {internal.word_a} / {internal.word_b}",
                f"{tr('rhy.internal')} · {tr('rep.lines_col')} {internal.line}",
                color=theme.color("muted"),
                on_click=lambda n=internal.line: self.app.focus_line(n),
            )

    def find_rhymes(self) -> None:
        word = self.find_entry.get().strip()
        if not word:
            return
        pool = words_from_text(self.app.get_text())
        results = find_rhymes(word, self._lang, extra_pool=pool)
        self.list.clear()
        if not results:
            self.list.show_empty(tr("rhy.no_candidates"))
            return
        for cand in results:
            quality = tr(QUALITY_KEYS.get(cand.quality, "rhy.type_slant"))
            color = (theme.color("good") if cand.quality == QUALITY_PERFECT
                     else theme.color("warn") if cand.quality == QUALITY_SLANT
                     else theme.color("muted"))
            self.list.add_row(
                cand.word,
                f"{quality} · {cand.syllables} {tr('syl.unit')}",
                color=color,
                # kropka oznacza slowo znalezione we wlasnym tekscie autora
                badge="•" if cand.source == "text" else "",
                on_click=lambda w=cand.word: self.app.insert_text(w),
            )


# --------------------------------------------------------------------------
# POWTORZENIA
# --------------------------------------------------------------------------

class RepetitionPanel(BasePanel):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_rowconfigure(5, weight=1)

        self.title = SectionTitle(self, text=tr("rep.header"))
        self.title.grid(row=0, column=0, sticky="ew", pady=(4, 8))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        controls.grid_columnconfigure(1, weight=1)

        self.min_label = ctk.CTkLabel(controls, text=tr("rep.min_count"),
                                      font=theme.font(size=12), anchor="w")
        self.min_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.min_var = ctk.StringVar(value=str(app.settings.get("repetition_min_count", 2)))
        self.min_menu = ctk.CTkOptionMenu(
            controls, values=["2", "3", "4", "5"], variable=self.min_var,
            width=70, command=lambda _v: self.app.request_analysis(force=True),
        )
        self.min_menu.grid(row=0, column=1, sticky="w")

        self.stop_var = ctk.BooleanVar(
            value=bool(app.settings.get("repetition_ignore_stopwords", True))
        )
        self.stop_cb = ctk.CTkCheckBox(
            self, text=tr("rep.ignore_stopwords"), variable=self.stop_var,
            command=lambda: self.app.request_analysis(force=True),
            font=theme.font(size=12),
        )
        self.stop_cb.grid(row=2, column=0, sticky="w", pady=(0, 8))

        self.stats = StatGrid(self, columns=2)
        self.stats.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        self.hint = Hint(self, text=tr("rep.hint"))
        self.hint.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        self.list = ScrollList(self, empty_text=tr("rep.none"))
        self.list.grid(row=5, column=0, sticky="nsew")

    def refresh_labels(self) -> None:
        self.title.configure(text=tr("rep.header"))
        self.min_label.configure(text=tr("rep.min_count"))
        self.stop_cb.configure(text=tr("rep.ignore_stopwords"))
        self.hint.configure(text=tr("rep.hint"))
        self.list.set_empty_text(tr("rep.none"))

    def refresh_theme(self) -> None:
        self.hint.refresh_theme()

    def update_report(self, text: str, lang: str) -> None:
        try:
            min_count = int(self.min_var.get())
        except ValueError:
            min_count = 2
        ignore = self.stop_var.get()
        self.app.settings.set("repetition_min_count", min_count)
        self.app.settings.set("repetition_ignore_stopwords", ignore)

        report = analyze_repetition(text, lang, min_count=min_count,
                                    ignore_stopwords=ignore)

        self.stats.set_items([
            (tr("syl.words"), str(report.total_words), None),
            (tr("rep.unique"), str(report.unique_words), None),
            (tr("rep.diversity"), f"{report.diversity:.0f}%",
             theme.score_color(report.diversity)),
            (tr("rep.words"), str(len(report.words)), None),
        ])

        self.app.highlight_repeats([r.value for r in report.words[:12]])

        self.list.clear()
        if not (report.words or report.phrases or report.lines):
            self.list.show_empty(tr("rep.none"))
            return

        if report.lines:
            self._header(tr("rep.lines"))
            for item in report.lines[:15]:
                self.list.add_row(
                    item.value[:80],
                    f"{tr('rep.lines_col')}: {', '.join(str(n) for n in item.lines)}",
                    color=theme.color("accent"),
                    badge=f"{item.count}×",
                    on_click=lambda n=item.lines[0]: self.app.focus_line(n),
                )

        if report.phrases:
            self._header(tr("rep.phrases"))
            for item in report.phrases[:20]:
                self.list.add_row(
                    f"„{item.value}”",
                    f"{tr('rep.lines_col')}: {', '.join(str(n) for n in item.lines)}",
                    color=theme.color("warn"),
                    badge=f"{item.count}×",
                    on_click=lambda n=item.lines[0]: self.app.focus_line(n),
                )

        if report.words:
            self._header(tr("rep.words"))
            for item in report.words[:30]:
                self.list.add_row(
                    item.value,
                    f"{tr('rep.lines_col')}: {', '.join(str(n) for n in item.lines[:12])}",
                    badge=f"{item.count}×",
                    on_click=lambda n=item.lines[0]: self.app.focus_line(n),
                )

    def _header(self, text: str) -> None:
        lbl = ctk.CTkLabel(self.list, text=text.upper(), anchor="w",
                           text_color=theme.color("muted"),
                           font=theme.font(size=11, weight="bold"))
        lbl.grid(row=len(self.list._widgets), column=0, sticky="ew",
                 padx=4, pady=(10, 2))
        self.list._widgets.append(lbl)


# --------------------------------------------------------------------------
# CZYTELNOSC
# --------------------------------------------------------------------------

class ReadabilityPanel(BasePanel):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_rowconfigure(6, weight=1)

        self.title = SectionTitle(self, text=tr("read.header"))
        self.title.grid(row=0, column=0, sticky="ew", pady=(4, 10))

        self.score_meter = MeterBar(self, label=tr("read.score"))
        self.score_meter.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.sing_meter = MeterBar(self, label=tr("read.singability"))
        self.sing_meter.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.level_label = ctk.CTkLabel(self, text="", anchor="w",
                                        font=theme.font(size=13, weight="bold"))
        self.level_label.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self.stats = StatGrid(self, columns=2)
        self.stats.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.hint = Hint(self, text=tr("read.hint"))
        self.hint.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        self.list = ScrollList(self)
        self.list.grid(row=6, column=0, sticky="nsew")

    def refresh_labels(self) -> None:
        self.title.configure(text=tr("read.header"))
        self.score_meter.set_label(tr("read.score"))
        self.sing_meter.set_label(tr("read.singability"))
        self.hint.configure(text=tr("read.hint"))

    def refresh_theme(self) -> None:
        self.hint.refresh_theme()

    def update_report(self, text: str, lang: str) -> None:
        report = analyze_readability(text, lang)

        self.score_meter.set_value(report.score)
        self.sing_meter.set_value(report.singability)
        self.level_label.configure(
            text=f"{tr('read.grade')}: {tr(report.level_key)}",
            text_color=theme.score_color(report.score),
        )

        items = [
            (tr("read.avg_sentence"), f"{report.avg_sentence_len:.1f}", None),
            (tr("read.avg_word"), f"{report.avg_word_len:.1f}", None),
            (tr("read.long_words"),
             f"{report.long_words} ({report.long_words_pct:.0f}%)",
             theme.color("warn") if report.long_words_pct > 12 else None),
            (tr("syl.total_syllables"), str(report.syllables), None),
        ]
        if lang == "en":
            items.insert(0, (tr("read.flesch"), f"{report.flesch:.0f}", None))
            items.insert(1, (tr("read.fk"), f"{report.flesch_kincaid:.1f}", None))
        else:
            items.insert(0, (tr("read.fog"), f"{report.fog:.1f}", None))
            items.insert(1, (tr("read.pisarek"), f"{report.pisarek:.1f}", None))
        self.stats.set_items(items)

        self.list.clear()
        if not report.hard_lines:
            self.list.show_empty(tr("read.no_hard_lines"))
            return
        lbl = ctk.CTkLabel(self.list, text=tr("read.hard_lines").upper(), anchor="w",
                           text_color=theme.color("muted"),
                           font=theme.font(size=11, weight="bold"))
        lbl.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        self.list._widgets.append(lbl)
        for number, line, syllables in report.hard_lines[:25]:
            self.list.add_row(
                line[:80],
                f"{tr('rep.lines_col')} {number}",
                color=theme.color("bad"),
                badge=f"{syllables} syl.",
                on_click=lambda n=number: self.app.focus_line(n),
            )
