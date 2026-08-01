"""Silnik OpenRouter - dostep do modeli w chmurze przez jedno API."""

from __future__ import annotations

import json
from typing import Iterator

import requests

from .base import AIEngine, AIError, CancelToken, ChatMessage

BASE_URL = "https://openrouter.ai/api/v1"
REFERER = "https://github.com/lyrics-manager-pro"
TITLE = "Lyrics Manager Pro"

# Sensowny zestaw startowy, gdy nie udalo sie pobrac listy z serwera.
FALLBACK_MODELS = [
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-opus-4.1",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-large",
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat",
]


class OpenRouterEngine(AIEngine):
    name = "openrouter"

    def __init__(self, api_key: str, timeout: int = 120) -> None:
        self.api_key = (api_key or "").strip()
        self.timeout = timeout

    # -- pomocnicze -------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise AIError("MISSING_KEY")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": REFERER,
            "X-Title": TITLE,
        }

    # -- modele -----------------------------------------------------------

    def list_models(self) -> list[str]:
        if not self.api_key:
            raise AIError("MISSING_KEY")
        try:
            resp = requests.get(
                f"{BASE_URL}/models", headers=self._headers(), timeout=30
            )
        except requests.RequestException as exc:
            raise AIError(str(exc)) from exc
        if resp.status_code == 401:
            raise AIError("Nieprawidlowy klucz API / Invalid API key")
        if resp.status_code >= 400:
            raise AIError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json().get("data", [])
        except ValueError as exc:
            raise AIError("Nieczytelna odpowiedz serwera / Malformed response") from exc
        models = sorted({item["id"] for item in data if item.get("id")})
        return models or list(FALLBACK_MODELS)

    def test_connection(self) -> None:
        models = self.list_models()
        if not models:
            raise AIError("Brak modeli / No models returned")

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
            "temperature": float(temperature),
            "stream": True,
        }
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=self._headers(),
                json=payload,
                stream=True,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise AIError(str(exc)) from exc

        if resp.status_code >= 400:
            detail = resp.text[:300]
            resp.close()
            if resp.status_code == 401:
                raise AIError("Nieprawidlowy klucz API / Invalid API key")
            if resp.status_code == 402:
                raise AIError("Brak srodkow na koncie OpenRouter / Insufficient credits")
            raise AIError(f"HTTP {resp.status_code}: {detail}")

        try:
            for raw in resp.iter_lines(decode_unicode=True):
                if cancel and cancel.cancelled:
                    break
                if not raw:
                    continue
                if raw.startswith(": "):        # komentarz keep-alive
                    continue
                if not raw.startswith("data:"):
                    continue
                data = raw[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except ValueError:
                    continue
                for choice in chunk.get("choices", []):
                    piece = (choice.get("delta") or {}).get("content")
                    if piece:
                        yield piece
        finally:
            resp.close()
