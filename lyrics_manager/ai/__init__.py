"""Silniki AI: OpenRouter (chmura) i Ollama (lokalnie)."""

from .base import AIEngine, AIError, ChatMessage
from .openrouter import OpenRouterEngine
from .ollama import OllamaEngine

__all__ = ["AIEngine", "AIError", "ChatMessage", "OpenRouterEngine", "OllamaEngine"]
