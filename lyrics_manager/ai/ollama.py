"""Silnik Ollama - modele uruchamiane lokalnie, bez wysylania tekstu w swiat."""

from __future__ import annotations

import json
from typing import Iterator

import requests

from .base import AIEngine, AIError, CancelToken, ChatMessage


class OllamaEngine(AIEngine):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300) -> None:
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.timeout = timeout

    # -- modele -----------------------------------------------------------

    def list_models(self) -> list[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
        except requests.RequestException as exc:
            raise AIError("NO_CONNECTION") from exc
        if resp.status_code >= 400:
            raise AIError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json().get("models", [])
        except ValueError as exc:
            raise AIError("Nieczytelna odpowiedz Ollama / Malformed Ollama response") from exc
        return sorted(m["name"] for m in data if m.get("name"))

    def test_connection(self) -> None:
        models = self.list_models()
        if not models:
            raise AIError(
                "Ollama dziala, ale nie ma zadnego modelu. Pobierz np.: ollama pull llama3.1"
            )

    # -- generowanie ------------------------------------------------------

    def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.8,
        cancel: CancelToken | None = None,
    ) -> Iterator[str]:
        payload = {
            "model": model,
            "messages": [m.as_dict() for m in messages],
            "stream": True,
            "options": {"temperature": float(temperature)},
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat", json=payload, stream=True, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise AIError("NO_CONNECTION") from exc

        if resp.status_code == 404:
            resp.close()
            raise AIError(
                f"Model '{model}' nie jest pobrany. Uruchom: ollama pull {model}"
            )
        if resp.status_code >= 400:
            detail = resp.text[:300]
            resp.close()
            raise AIError(f"HTTP {resp.status_code}: {detail}")

        try:
            for raw in resp.iter_lines(decode_unicode=True):
                if cancel and cancel.cancelled:
                    break
                if not raw:
                    continue
                try:
                    chunk = json.loads(raw)
                except ValueError:
                    continue
                if chunk.get("error"):
                    raise AIError(str(chunk["error"]))
                piece = (chunk.get("message") or {}).get("content")
                if piece:
                    yield piece
                if chunk.get("done"):
                    break
        finally:
            resp.close()
