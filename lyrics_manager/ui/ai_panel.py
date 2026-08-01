"""Panel asystenta AI - OpenRouter i Ollama, streaming odpowiedzi."""

from __future__ import annotations

import queue
import threading

import customtkinter as ctk

from ..ai.base import AIError, CancelToken, ChatMessage
from ..ai.ollama import OllamaEngine
from ..ai.openrouter import FALLBACK_MODELS, OpenRouterEngine
from ..ai.prompts import TASKS, PromptContext, build_messages
from ..analysis.rhymes import analyze_rhymes
from ..analysis.syllables import analyze_syllables
from ..i18n import LANGUAGE_LABELS, tr
from . import theme
from .editor import ReadOnlyText
from .widgets import SectionTitle, make_segmented

ENGINE_KEYS = ["ollama", "openrouter"]


class AIPanel(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self.settings = app.settings

        self._queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._cancel: CancelToken | None = None
        self._thread: threading.Thread | None = None
        self._models: dict[str, list[str]] = {"ollama": [], "openrouter": []}

        self.grid_columnconfigure(0, weight=1)

        row = 0
        self.title = SectionTitle(self, text=tr("ai.header"))
        self.title.grid(row=row, column=0, sticky="ew", pady=(4, 8))
        row += 1

        # --- silnik + model
        engine_frame = ctk.CTkFrame(self, fg_color="transparent")
        engine_frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        engine_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self.engine_label = ctk.CTkLabel(engine_frame, text=tr("ai.engine"), anchor="w",
                                         font=theme.font(size=12))
        self.engine_label.grid(row=0, column=0, sticky="w")
        self.engine_menu = make_segmented(
            engine_frame, values=self._engine_values(), command=self._on_engine_change,
        )
        self.engine_menu.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        model_frame = ctk.CTkFrame(self, fg_color="transparent")
        model_frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        model_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self.model_label = ctk.CTkLabel(model_frame, text=tr("ai.model"), anchor="w",
                                        font=theme.font(size=12))
        self.model_label.grid(row=0, column=0, sticky="w")
        self.model_var = ctk.StringVar(value="")
        self.model_menu = ctk.CTkOptionMenu(model_frame, values=["—"],
                                            variable=self.model_var, dynamic_resizing=False)
        self.model_menu.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(2, 0))
        self.refresh_btn = ctk.CTkButton(model_frame, text="⟳", width=36,
                                         command=self.refresh_models)
        self.refresh_btn.grid(row=1, column=1, pady=(2, 0))

        # --- zadanie
        self.task_label = ctk.CTkLabel(self, text=tr("ai.task"), anchor="w",
                                       font=theme.font(size=12))
        self.task_label.grid(row=row, column=0, sticky="w")
        row += 1
        self.task_var = ctk.StringVar(value=tr("task.alternatives"))
        self.task_menu = ctk.CTkOptionMenu(self, values=self._task_values(),
                                           variable=self.task_var, dynamic_resizing=False)
        self.task_menu.grid(row=row, column=0, sticky="ew", pady=(2, 6))
        row += 1

        # --- zakres + jezyk odpowiedzi
        opts = ctk.CTkFrame(self, fg_color="transparent")
        opts.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        opts.grid_columnconfigure(0, weight=1)
        opts.grid_columnconfigure(1, weight=1)
        row += 1

        self.scope_label = ctk.CTkLabel(opts, text=tr("ai.scope"), anchor="w",
                                        font=theme.font(size=12))
        self.scope_label.grid(row=0, column=0, sticky="w")
        self.scope_var = ctk.StringVar(value=tr("ai.scope.whole"))
        self.scope_menu = ctk.CTkOptionMenu(
            opts, values=[tr("ai.scope.selection"), tr("ai.scope.whole")],
            variable=self.scope_var, dynamic_resizing=False,
        )
        self.scope_menu.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(2, 0))

        self.outlang_label = ctk.CTkLabel(opts, text=tr("ai.out_lang"), anchor="w",
                                          font=theme.font(size=12))
        self.outlang_label.grid(row=0, column=1, sticky="w")
        self.outlang_var = ctk.StringVar(
            value=LANGUAGE_LABELS.get(self.settings.get("ai_output_language", "pl"), "Polski")
        )
        self.outlang_menu = ctk.CTkOptionMenu(
            opts, values=list(LANGUAGE_LABELS.values()), variable=self.outlang_var,
            command=self._on_outlang_change, dynamic_resizing=False,
        )
        self.outlang_menu.grid(row=1, column=1, sticky="ew", pady=(2, 0))

        # --- kreatywnosc
        temp_frame = ctk.CTkFrame(self, fg_color="transparent")
        temp_frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        temp_frame.grid_columnconfigure(0, weight=1)
        row += 1
        self.temp_label = ctk.CTkLabel(
            temp_frame, text=f"{tr('ai.temperature')}: "
                             f"{float(self.settings.get('ai_temperature', 0.8)):.1f}",
            anchor="w", font=theme.font(size=12),
        )
        self.temp_label.grid(row=0, column=0, sticky="w")
        self.temp_slider = ctk.CTkSlider(temp_frame, from_=0.0, to=1.5,
                                         number_of_steps=15, command=self._on_temp)
        self.temp_slider.set(float(self.settings.get("ai_temperature", 0.8)))
        self.temp_slider.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # --- dodatkowe wskazowki
        self.extra_label = ctk.CTkLabel(self, text=tr("ai.instruction"), anchor="w",
                                        font=theme.font(size=12))
        self.extra_label.grid(row=row, column=0, sticky="w")
        row += 1
        self.extra_box = ctk.CTkTextbox(self, height=60, font=theme.font(size=12))
        self.extra_box.grid(row=row, column=0, sticky="ew", pady=(2, 8))
        row += 1

        # --- przyciski uruchomienia
        run_frame = ctk.CTkFrame(self, fg_color="transparent")
        run_frame.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        run_frame.grid_columnconfigure(0, weight=1)
        run_frame.grid_columnconfigure(1, weight=1)
        row += 1
        self.grid_rowconfigure(row - 1, minsize=40)
        self.run_btn = ctk.CTkButton(run_frame, text=tr("ai.run"), command=self.run)
        self.run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.stop_btn = ctk.CTkButton(run_frame, text=tr("ai.stop"), command=self.stop,
                                      fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT, state="disabled")
        self.stop_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # --- wynik
        self.output = ReadOnlyText(self, font_size=12)
        self.output.grid(row=row, column=0, sticky="nsew", pady=(0, 6))
        self.grid_rowconfigure(row, weight=1)
        row += 1

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=row, column=0, sticky="ew")
        for c in range(4):
            actions.grid_columnconfigure(c, weight=1)
        self.insert_btn = ctk.CTkButton(actions, text=tr("ai.insert"), height=28,
                                        command=self._insert, font=theme.font(size=11))
        self.insert_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.replace_btn = ctk.CTkButton(actions, text=tr("ai.replace"), height=28,
                                         command=self._replace, font=theme.font(size=11))
        self.replace_btn.grid(row=0, column=1, sticky="ew", padx=3)
        self.copy_btn = ctk.CTkButton(actions, text=tr("ai.copy"), height=28,
                                      fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
                                      command=self._copy, font=theme.font(size=11))
        self.copy_btn.grid(row=0, column=2, sticky="ew", padx=3)
        self.clear_btn = ctk.CTkButton(actions, text=tr("ai.clear"), height=28,
                                       fg_color="transparent", border_width=1, text_color=theme.GHOST_TEXT,
                                       command=self.output.clear, font=theme.font(size=11))
        self.clear_btn.grid(row=0, column=3, sticky="ew", padx=(3, 0))

        self._apply_engine(self.settings.get("ai_engine", "ollama"), initial=True)
        self._poll_queue()

    # -- etykiety ---------------------------------------------------------

    def _engine_values(self) -> list[str]:
        return [tr("ai.engine.ollama"), tr("ai.engine.openrouter")]

    def _task_values(self) -> list[str]:
        return [tr(f"task.{t}") for t in TASKS]

    def _current_task(self) -> str:
        label = self.task_var.get()
        for task in TASKS:
            if tr(f"task.{task}") == label:
                return task
        return "alternatives"

    def _current_engine(self) -> str:
        return "openrouter" if self.engine_menu.get() == tr("ai.engine.openrouter") else "ollama"

    def refresh_labels(self) -> None:
        task = self._current_task()
        scope_whole = self.scope_var.get() != tr("ai.scope.selection")
        engine = self._current_engine()

        self.title.configure(text=tr("ai.header"))
        self.engine_label.configure(text=tr("ai.engine"))
        self.engine_menu.configure(values=self._engine_values())
        self.engine_menu.set(tr(f"ai.engine.{engine}"))
        self.model_label.configure(text=tr("ai.model"))
        self.task_label.configure(text=tr("ai.task"))
        self.task_menu.configure(values=self._task_values())
        self.task_var.set(tr(f"task.{task}"))
        self.scope_label.configure(text=tr("ai.scope"))
        self.scope_menu.configure(values=[tr("ai.scope.selection"), tr("ai.scope.whole")])
        self.scope_var.set(tr("ai.scope.whole") if scope_whole else tr("ai.scope.selection"))
        self.outlang_label.configure(text=tr("ai.out_lang"))
        self.temp_label.configure(
            text=f"{tr('ai.temperature')}: {self.temp_slider.get():.1f}"
        )
        self.extra_label.configure(text=tr("ai.instruction"))
        self.run_btn.configure(text=tr("ai.run"))
        self.stop_btn.configure(text=tr("ai.stop"))
        self.insert_btn.configure(text=tr("ai.insert"))
        self.replace_btn.configure(text=tr("ai.replace"))
        self.copy_btn.configure(text=tr("ai.copy"))
        self.clear_btn.configure(text=tr("ai.clear"))

    def refresh_theme(self) -> None:
        self.output.refresh_theme()

    # -- ustawienia -------------------------------------------------------

    def _on_engine_change(self, _value: str) -> None:
        self._apply_engine(self._current_engine())

    def _apply_engine(self, engine: str, initial: bool = False) -> None:
        self.settings.set("ai_engine", engine)
        self.engine_menu.set(tr(f"ai.engine.{engine}"))
        cached = self._models.get(engine) or []
        default = self.settings.get(
            "openrouter_model" if engine == "openrouter" else "ollama_model", ""
        )
        values = cached or ([default] if default else ["—"])
        self.model_menu.configure(values=values)
        self.model_var.set(default if default in values else values[0])
        if not cached:
            self.refresh_models(silent=True)

    def _on_outlang_change(self, value: str) -> None:
        for code, label in LANGUAGE_LABELS.items():
            if label == value:
                self.settings.set("ai_output_language", code)
                break

    def _on_temp(self, value: float) -> None:
        self.settings.set("ai_temperature", round(float(value), 2))
        self.temp_label.configure(text=f"{tr('ai.temperature')}: {float(value):.1f}")

    def output_language(self) -> str:
        label = self.outlang_var.get()
        for code, name in LANGUAGE_LABELS.items():
            if name == label:
                return code
        return "pl"

    # -- modele -----------------------------------------------------------

    def build_engine(self):
        engine = self._current_engine()
        if engine == "openrouter":
            return OpenRouterEngine(self.settings.get("openrouter_api_key", ""))
        return OllamaEngine(self.settings.get("ollama_url", "http://localhost:11434"))

    def refresh_models(self, silent: bool = False) -> None:
        engine_name = self._current_engine()
        engine = self.build_engine()

        def work() -> None:
            try:
                models = engine.list_models()
                self._queue.put(("models", f"{engine_name}\x00" + "\x00".join(models)))
            except AIError as exc:
                if not silent:
                    self._queue.put(("error", self._friendly_error(exc, engine_name)))
                elif engine_name == "openrouter" and str(exc) != "MISSING_KEY":
                    self._queue.put(
                        ("models", "openrouter\x00" + "\x00".join(FALLBACK_MODELS))
                    )

        threading.Thread(target=work, daemon=True).start()

    def _friendly_error(self, exc: Exception, engine_name: str) -> str:
        text = str(exc)
        if text == "MISSING_KEY":
            return tr("ai.no_key")
        if text == "NO_CONNECTION":
            return tr("ai.no_ollama")
        return f"{tr('msg.error')}: {text}"

    # -- generowanie ------------------------------------------------------

    def run(self, preset_task: str | None = None, preset_word: str = "") -> None:
        if self._thread and self._thread.is_alive():
            return

        if preset_task:
            self.task_var.set(tr(f"task.{preset_task}"))

        task = preset_task or self._current_task()
        whole = self.scope_var.get() != tr("ai.scope.selection")
        full_text = self.app.get_text()
        fragment = full_text if whole else (self.app.get_selection() or full_text)

        if not fragment.strip() and task not in {"rhymes"}:
            self.app.set_status(tr("ai.empty_input"), kind="warn")
            return

        model = self.model_var.get()
        if not model or model == "—":
            self.app.set_status(tr("ai.no_models"), kind="warn")
            self.refresh_models()
            return

        text_lang = self.app.text_language()
        syl = analyze_syllables(fragment, text_lang)
        rhy = analyze_rhymes(fragment, text_lang)

        ctx = PromptContext(
            task=task,
            text=fragment,
            full_text=full_text,
            text_lang=text_lang,
            out_lang=self.output_language(),
            extra=self.extra_box.get("1.0", "end-1c"),
            title=self.app.document.meta.title,
            artist=self.app.document.meta.artist,
            style=self.app.document.meta.style,
            syllables_per_line=[ln.syllables for ln in syl.lines],
            rhyme_scheme=rhy.scheme,
            target_word=preset_word,
        )
        messages = build_messages(ctx)

        engine = self.build_engine()
        engine_name = self._current_engine()
        temperature = float(self.temp_slider.get())
        cancel = CancelToken()
        self._cancel = cancel

        self.output.clear()
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.app.set_status(tr("ai.working"), kind="info", busy=True)

        def work() -> None:
            try:
                for chunk in engine.stream_chat(messages, model, temperature, cancel):
                    self._queue.put(("chunk", chunk))
                self._queue.put(("done", "" if not cancel.cancelled else "cancelled"))
            except AIError as exc:
                self._queue.put(("error", self._friendly_error(exc, engine_name)))
            except Exception as exc:  # noqa: BLE001
                self._queue.put(("error", f"{tr('msg.error')}: {exc}"))

        self._thread = threading.Thread(target=work, daemon=True)
        self._thread.start()

    def run_rhyme_task(self, word: str) -> None:
        self.run(preset_task="rhymes", preset_word=word)

    def stop(self) -> None:
        if self._cancel:
            self._cancel.cancel()
        self.stop_btn.configure(state="disabled")

    # -- petla komunikatow z watku ----------------------------------------

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "chunk":
                    self.output.append(payload)
                elif kind == "done":
                    self.run_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.app.set_status(
                        tr("ai.stopped") if payload == "cancelled" else tr("ai.done"),
                        kind="ok",
                    )
                elif kind == "error":
                    self.run_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    self.app.set_status(payload, kind="error")
                    if not self.output.get_content().strip():
                        self.output.set_content(payload)
                elif kind == "models":
                    engine_name, _, joined = payload.partition("\x00")
                    models = [m for m in joined.split("\x00") if m]
                    self._models[engine_name] = models
                    if engine_name == self._current_engine() and models:
                        self.model_menu.configure(values=models)
                        default = self.settings.get(
                            "openrouter_model" if engine_name == "openrouter"
                            else "ollama_model", ""
                        )
                        self.model_var.set(default if default in models else models[0])
        except queue.Empty:
            pass
        self.after(60, self._poll_queue)

    # -- akcje na wyniku --------------------------------------------------

    def _result(self) -> str:
        return self.output.get_content().strip()

    def _insert(self) -> None:
        content = self._result()
        if content:
            self.app.insert_text("\n" + content + "\n")

    def _replace(self) -> None:
        content = self._result()
        if not content:
            return
        if self.scope_var.get() == tr("ai.scope.selection"):
            self.app.replace_selection(content)
        else:
            self.app.set_text(content)

    def _copy(self) -> None:
        content = self._result()
        if content:
            self.app.copy_to_clipboard(content)
