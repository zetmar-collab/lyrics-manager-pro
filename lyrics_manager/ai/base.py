"""Wspolny interfejs silnikow AI."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Iterator


class AIError(RuntimeError):
    """Blad komunikacji z silnikiem AI - komunikat jest gotowy do pokazania."""


@dataclass
class ChatMessage:
    role: str      # "system" | "user" | "assistant"
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class CancelToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


class AIEngine:
    """Bazowy silnik. Implementacje musza dostarczyc `stream_chat` i `list_models`."""

    name = "base"

    def list_models(self) -> list[str]:
        raise NotImplementedError

    def test_connection(self) -> None:
        """Rzuca AIError, jesli polaczenie nie dziala."""
        self.list_models()

    def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.8,
        cancel: CancelToken | None = None,
    ) -> Iterator[str]:
        raise NotImplementedError

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.8,
        cancel: CancelToken | None = None,
    ) -> str:
        return "".join(self.stream_chat(messages, model, temperature, cancel))


def run_in_thread(
    fn: Callable[[], None],
    on_error: Callable[[Exception], None] | None = None,
) -> threading.Thread:
    def wrapper() -> None:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - blad ma trafic do UI, nie ubic watku
            if on_error:
                on_error(exc)

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return thread
