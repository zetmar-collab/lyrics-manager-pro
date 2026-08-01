"""Wspolne narzedzia tekstowe dla modulow analitycznych."""

from __future__ import annotations

import re
import unicodedata

# Znacznik sekcji: [Zwrotka 1], [Chorus], {Refren} itp.
SECTION_RE = re.compile(r"^\s*[\[\({](?P<name>[^\]\)}]{1,60})[\]\)}]\s*$")

# Slowo: litery (z polskimi znakami) + apostrofy i lacznik wewnatrz slowa.
WORD_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)

SENTENCE_SPLIT_RE = re.compile(r"[.!?…]+[\s\"')\]]*|\n{2,}")

PL_STOPWORDS = {
    "a", "aby", "ale", "albo", "ani", "az", "az", "bez", "bo", "by", "byc", "byl", "byla",
    "byli", "bylo", "byly", "co", "coz", "czy", "czyli", "dla", "do", "gdy", "gdyby", "gdzie",
    "go", "i", "ich", "ile", "im", "inne", "iz", "ja", "jak", "jakby", "jaki", "je", "jego",
    "jej", "jest", "jestem", "jesli", "juz", "ka", "kiedy", "kto", "ktora", "ktore", "ktory",
    "ku", "lecz", "lub", "ma", "mam", "mi", "mnie", "moj", "moja", "moze", "mu", "my", "na",
    "nad", "nam", "nas", "nasz", "nawet", "nic", "nie", "nim", "niz", "no", "o", "od", "oraz",
    "po", "pod", "ponad", "poniewaz", "przed", "przez", "przy", "sa", "sie", "sobie", "swoje",
    "ta", "tak", "takze", "tam", "te", "tego", "tej", "temu", "ten", "teraz", "tez", "to",
    "tu", "tylko", "tym", "u", "w", "we", "wiec", "wszystko", "z", "za", "ze", "zeby", "zas",
    "on", "ona", "ono", "oni", "one", "ty", "wy", "sobie", "cie", "ci", "wam", "was", "jak",
}

EN_STOPWORDS = {
    "a", "about", "all", "am", "an", "and", "any", "are", "as", "at", "be", "been", "but",
    "by", "can", "did", "do", "does", "for", "from", "had", "has", "have", "he", "her",
    "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just",
    "me", "my", "no", "not", "of", "on", "or", "our", "out", "she", "so", "some", "than",
    "that", "the", "their", "them", "then", "there", "these", "they", "this", "to", "too",
    "up", "us", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will",
    "with", "would", "you", "your", "yours", "aint", "cant", "dont", "im", "ive", "youre",
    "its", "thats", "gonna", "wanna",
}


def stopwords(lang: str) -> set[str]:
    return PL_STOPWORDS if lang == "pl" else EN_STOPWORDS


def strip_accents(text: str) -> str:
    """Usuwa znaki diakrytyczne (do porownan i normalizacji)."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def is_section_marker(line: str) -> bool:
    return bool(SECTION_RE.match(line))


def section_name(line: str) -> str | None:
    m = SECTION_RE.match(line)
    return m.group("name").strip() if m else None


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def lowered_words(text: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def sentences(text: str) -> list[str]:
    """Zdania. Dla tekstow piosenek wers bez interpunkcji traktujemy jak zdanie."""
    stripped = "\n".join(
        line for line in text.splitlines() if line.strip() and not is_section_marker(line)
    )
    if not stripped.strip():
        return []
    parts = [p.strip() for p in SENTENCE_SPLIT_RE.split(stripped) if p and p.strip()]
    if len(parts) <= 1:
        # brak interpunkcji koncowej - kazdy wers to jednostka
        parts = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    return parts


def content_lines(text: str) -> list[tuple[int, str]]:
    """Wersy z trescia (bez pustych i bez znacznikow sekcji), z numerem wersu 1-based."""
    out: list[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if line.strip() and not is_section_marker(line):
            out.append((idx, line))
    return out
