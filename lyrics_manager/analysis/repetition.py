"""Wyszukiwanie powtorzen: slowa, frazy (n-gramy) i cale wersy."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .text_utils import WORD_RE, content_lines, stopwords


@dataclass
class RepeatedItem:
    value: str
    count: int
    lines: list[int] = field(default_factory=list)
    words: int = 1


@dataclass
class RepetitionReport:
    words: list[RepeatedItem] = field(default_factory=list)
    phrases: list[RepeatedItem] = field(default_factory=list)
    lines: list[RepeatedItem] = field(default_factory=list)
    total_words: int = 0
    unique_words: int = 0
    diversity: float = 0.0       # TTR w procentach
    top_word: str = ""


def analyze_repetition(
    text: str,
    lang: str = "pl",
    min_count: int = 2,
    ignore_stopwords: bool = True,
    max_ngram: int = 5,
) -> RepetitionReport:
    report = RepetitionReport()
    stops = stopwords(lang) if ignore_stopwords else set()

    lines = content_lines(text)
    if not lines:
        return report

    word_positions: dict[str, list[int]] = defaultdict(list)
    all_words: list[str] = []
    line_tokens: list[tuple[int, list[str]]] = []

    for number, raw in lines:
        tokens = [w.lower() for w in WORD_RE.findall(raw)]
        line_tokens.append((number, tokens))
        all_words.extend(tokens)
        for tok in tokens:
            word_positions[tok].append(number)

    report.total_words = len(all_words)
    report.unique_words = len(set(all_words))
    report.diversity = (100.0 * report.unique_words / report.total_words) if all_words else 0.0

    # --- pojedyncze slowa
    for word, positions in word_positions.items():
        if len(word) < 2 or word in stops:
            continue
        if len(positions) >= min_count:
            report.words.append(RepeatedItem(word, len(positions), sorted(set(positions))))
    report.words.sort(key=lambda r: (-r.count, r.value))
    if report.words:
        report.top_word = report.words[0].value

    # --- frazy (n-gramy w obrebie wersu)
    ngram_positions: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for number, tokens in line_tokens:
        for n in range(2, max_ngram + 1):
            for i in range(len(tokens) - n + 1):
                gram = tuple(tokens[i: i + n])
                if all(t in stops for t in gram):
                    continue
                ngram_positions[gram].append(number)

    phrase_items: list[RepeatedItem] = []
    for gram, positions in ngram_positions.items():
        if len(positions) >= min_count:
            phrase_items.append(
                RepeatedItem(" ".join(gram), len(positions), sorted(set(positions)), words=len(gram))
            )
    # usun frazy zawarte w dluzszych o tej samej liczbie wystapien
    phrase_items.sort(key=lambda r: (-r.words, -r.count))
    kept: list[RepeatedItem] = []
    for item in phrase_items:
        if any(item.value in k.value and item.count <= k.count for k in kept):
            continue
        kept.append(item)
    kept.sort(key=lambda r: (-r.count, -r.words, r.value))
    report.phrases = kept

    # --- cale wersy
    line_map: dict[str, list[int]] = defaultdict(list)
    for number, raw in lines:
        key = " ".join(w.lower() for w in WORD_RE.findall(raw))
        if key:
            line_map[key].append(number)
    for key, positions in line_map.items():
        if len(positions) >= min_count:
            original = next(raw.strip() for n, raw in lines if n == positions[0])
            report.lines.append(RepeatedItem(original, len(positions), positions,
                                             words=len(key.split())))
    report.lines.sort(key=lambda r: (-r.count, r.value))

    return report
