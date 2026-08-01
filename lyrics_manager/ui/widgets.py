"""Male, wielokrotnie uzywane elementy interfejsu."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from . import theme


class StatGrid(ctk.CTkFrame):
    """Siatka 'etykieta: wartosc' odswiezana w calosci."""

    def __init__(self, master, columns: int = 2, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._columns = columns
        self._rows: list[tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        for c in range(columns):
            self.grid_columnconfigure(c * 2 + 1, weight=1)

    def set_items(self, items: list[tuple[str, str, str | None]]) -> None:
        """items: [(etykieta, wartosc, kolor_lub_None)]"""
        for label, value in self._rows:
            label.destroy()
            value.destroy()
        self._rows.clear()

        muted = theme.color("muted")
        for i, (name, value, color) in enumerate(items):
            row, col = divmod(i, self._columns)
            lbl = ctk.CTkLabel(self, text=f"{name}:", anchor="w", text_color=muted,
                               font=theme.font(size=12))
            lbl.grid(row=row, column=col * 2, sticky="w", padx=(0, 6), pady=2)
            val = ctk.CTkLabel(self, text=value, anchor="w",
                               text_color=color or theme.default_text(),
                               font=theme.font(size=13, weight="bold"))
            val.grid(row=row, column=col * 2 + 1, sticky="w", padx=(0, 16), pady=2)
            self._rows.append((lbl, val))


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text: str = "", **kwargs):
        options = {"anchor": "w", "font": theme.font(size=15, weight="bold")}
        options.update(kwargs)
        super().__init__(master, text=text, **options)


class Hint(ctk.CTkLabel):
    def __init__(self, master, text: str = "", **kwargs):
        # kwargs moga nadpisac domyslne ustawienia (np. szersze zawijanie
        # w oknie dialogowym), dlatego laczymy slowniki zamiast rozpakowywac
        options = {
            "anchor": "w", "justify": "left", "wraplength": 380,
            "text_color": theme.color("muted"), "font": theme.font(size=11),
        }
        options.update(kwargs)
        super().__init__(master, text=text, **options)

    def refresh_theme(self) -> None:
        self.configure(text_color=theme.color("muted"))


class MeterBar(ctk.CTkFrame):
    """Pasek postepu z etykieta i wartoscia 0-100."""

    def __init__(self, master, label: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._label = ctk.CTkLabel(self, text=label, anchor="w", font=theme.font(size=12))
        self._label.grid(row=0, column=0, sticky="w")
        self._value = ctk.CTkLabel(self, text="-", anchor="e",
                                   font=theme.font(size=12, weight="bold"))
        self._value.grid(row=0, column=1, sticky="e")
        self._bar = ctk.CTkProgressBar(self, height=8)
        self._bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self._bar.set(0)

    def set_label(self, text: str) -> None:
        self._label.configure(text=text)

    def set_value(self, value: float, suffix: str = "/100") -> None:
        value = max(0.0, min(100.0, float(value)))
        self._bar.set(value / 100.0)
        col = theme.score_color(value)
        self._bar.configure(progress_color=col)
        self._value.configure(text=f"{value:.0f}{suffix}", text_color=col)


class ScrollList(ctk.CTkScrollableFrame):
    """Lista klikalnych wierszy - lzejsza alternatywa dla ttk.Treeview,
    ktora nie umie ladnie przejmowac motywu CustomTkinter."""

    def __init__(self, master, empty_text: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._widgets: list[ctk.CTkBaseClass] = []
        self._empty_text = empty_text

    def clear(self) -> None:
        for widget in self._widgets:
            widget.destroy()
        self._widgets.clear()

    def set_empty_text(self, text: str) -> None:
        self._empty_text = text

    def show_empty(self, text: str | None = None) -> None:
        self.clear()
        lbl = ctk.CTkLabel(self, text=text or self._empty_text, anchor="w",
                           text_color=theme.color("muted"), font=theme.font(size=12))
        lbl.grid(row=0, column=0, sticky="ew", pady=6, padx=4)
        self._widgets.append(lbl)

    def add_row(
        self,
        primary: str,
        secondary: str = "",
        color: str | None = None,
        on_click: Callable[[], None] | None = None,
        badge: str = "",
    ) -> None:
        row = len(self._widgets)
        frame = ctk.CTkFrame(self, fg_color=("gray92", "gray17"), corner_radius=6)
        frame.grid(row=row, column=0, sticky="ew", pady=2, padx=2)
        frame.grid_columnconfigure(0, weight=1)

        main = ctk.CTkLabel(frame, text=primary, anchor="w", justify="left",
                            text_color=color or theme.default_text(),
                            font=theme.font(size=12, weight="bold"))
        main.grid(row=0, column=0, sticky="ew", padx=8, pady=(5, 0))

        if badge:
            bl = ctk.CTkLabel(frame, text=badge, anchor="e",
                              text_color=theme.color("muted"), font=theme.font(size=11))
            bl.grid(row=0, column=1, sticky="e", padx=8)

        if secondary:
            sub = ctk.CTkLabel(frame, text=secondary, anchor="w", justify="left",
                               text_color=theme.color("muted"), font=theme.font(size=11))
            sub.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 5))
        else:
            main.grid_configure(pady=(5, 5))

        if on_click:
            for widget in (frame, main) + ((sub,) if secondary else ()):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda e, cb=on_click: cb())

        self._widgets.append(frame)


def make_segmented(master, **kwargs) -> ctk.CTkSegmentedButton:
    """CTkSegmentedButton z czytelnym kontrastem w obu motywach.

    Domyslnie CTk maluje etykiety niemal bialym kolorem, przez co segmenty
    nieaktywne gina na jasnym tle.
    """
    style = {
        "text_color": ("gray17", "#DCE4EE"),
        "selected_color": ("#BFDBFE", "#1D4ED8"),
        "selected_hover_color": ("#93C5FD", "#2563EB"),
        "unselected_color": ("gray86", "gray25"),
        "unselected_hover_color": ("gray78", "gray32"),
    }
    style.update(kwargs)
    return ctk.CTkSegmentedButton(master, **style)


class TabView(ctk.CTkFrame):
    """Zakladki z wlasnym paskiem przyciskow.

    W odroznieniu od CTkTabview pozwala zmienic etykiety zakladek bez
    niszczenia paneli - to konieczne przy przelaczaniu jezyka interfejsu.
    Panele sa dziecmi jednego kontenera, przelaczamy je grid/grid_remove.
    """

    def __init__(self, master, columns: int = 4, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._columns = columns
        self._names: list[str] = []
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._panels: dict[str, ctk.CTkBaseClass] = {}
        self._current: str | None = None
        self._on_change: Callable[[str], None] | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.bar = ctk.CTkFrame(self, fg_color="transparent")
        self.bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        for c in range(columns):
            self.bar.grid_columnconfigure(c, weight=1)

        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def set_change_callback(self, callback: Callable[[str], None]) -> None:
        self._on_change = callback

    def add(self, name: str, label: str, panel_factory: Callable[[ctk.CTkFrame], ctk.CTkBaseClass]):
        panel = panel_factory(self.content)
        self._panels[name] = panel
        self._names.append(name)

        index = len(self._names) - 1
        row, col = divmod(index, self._columns)
        button = ctk.CTkButton(
            self.bar, text=label, height=30, corner_radius=6, border_width=1,
            border_color=("gray75", "gray30"),
            font=theme.font(size=12), command=lambda n=name: self.select(n),
        )
        button.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
        self._buttons[name] = button

        if self._current is None:
            self.select(name)
        else:
            panel.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            panel.grid_remove()
            # przycisk powstal juz po ostatnim select() - trzeba go wystylowac,
            # inaczej zostalby z domyslnym wygladem zakladki aktywnej
            self._update_buttons()
        return panel

    def select(self, name: str) -> None:
        if name not in self._panels:
            return
        if self._current and self._current in self._panels:
            self._panels[self._current].grid_remove()
        self._current = name
        self._panels[name].grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._update_buttons()
        if self._on_change:
            self._on_change(name)

    def get(self) -> str | None:
        return self._current

    def panel(self, name: str):
        return self._panels.get(name)

    def set_label(self, name: str, label: str) -> None:
        if name in self._buttons:
            self._buttons[name].configure(text=label)

    def _update_buttons(self) -> None:
        for name, button in self._buttons.items():
            if name == self._current:
                button.configure(fg_color=("#2563EB", "#1D4ED8"), text_color="#FFFFFF")
            else:
                button.configure(fg_color="transparent",
                                 text_color=("gray20", "gray85"))

    def refresh_theme(self) -> None:
        self._update_buttons()


class Toolbar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._col = 0

    def add(self, widget, padx: tuple[int, int] | int = (0, 6), sticky: str = "w"):
        widget.grid(row=0, column=self._col, padx=padx, sticky=sticky)
        self._col += 1
        return widget

    def add_spacer(self):
        self.grid_columnconfigure(self._col, weight=1)
        spacer = ctk.CTkFrame(self, fg_color="transparent", width=1, height=1)
        spacer.grid(row=0, column=self._col, sticky="ew")
        self._col += 1
        return spacer
