"""Ocena czytelnosci tekstu piosenki.

Angielski: Flesch Reading Ease + Flesch-Kincaid Grade Level.
Polski:    indeks FOG (Gunninga) w adaptacji polskiej + indeks Pisarka.
Dodatkowo: wskaznik "spiewalnosci" liczony z rownomiernosci wersow,
gestosci sylab i udzialu dlugich wyrazow.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .syllables import analyze_syllables, count_syllables_word
from .text_utils import WORD_RE, content_lines, sentences


@dataclass
class ReadabilityReport:
    score: float = 0.0             # 0-100, im wyzej tym latwiej
    level_key: str = "read.level.medium"
    flesch: float = 0.0            # tylko EN
    flesch_kincaid: float = 0.0    # tylko EN
    fog: float = 0.0               # tylko PL
    pisarek: float = 0.0           # tylko PL
    words: int = 0
    sentences: int = 0
    syllables: int = 0
    long_words: int = 0
    long_words_pct: float = 0.0
    avg_word_len: float = 0.0
    avg_sentence_len: float = 0.0
    avg_syllables_per_word: float = 0.0
    singability: float = 0.0       # 0-100
    hard_lines: list[tuple[int, str, int]] = field(default_factory=list)
    language: str = "pl"


def _level_key(score: float) -> str:
    if score >= 80:
        return "read.level.very_easy"
    if score >= 65:
        return "read.level.easy"
    if score >= 45:
        return "read.level.medium"
    if score >= 30:
        return "read.level.hard"
    return "read.level.very_hard"


def analyze_readability(text: str, lang: str = "pl") -> ReadabilityReport:
    report = ReadabilityReport(language=lang)

    word_list = WORD_RE.findall(text)
    sent_list = sentences(text)
    if not word_list or not sent_list:
        return report

    syllable_counts = [count_syllables_word(w, lang) for w in word_list]
    report.words = len(word_list)
    report.sentences = len(sent_list)
    report.syllables = sum(syllable_counts)
    report.long_words = sum(1 for c in syllable_counts if c >= 4)
    report.long_words_pct = 100.0 * report.long_words / report.words
    report.avg_word_len = sum(len(w) for w in word_list) / report.words
    report.avg_sentence_len = report.words / report.sentences
    report.avg_syllables_per_word = report.syllables / report.words

    asl = report.avg_sentence_len
    asw = report.avg_syllables_per_word

    if lang == "en":
        report.flesch = 206.835 - 1.015 * asl - 84.6 * asw
        report.flesch_kincaid = 0.39 * asl + 11.8 * asw - 15.59
        report.score = max(0.0, min(100.0, report.flesch))
    else:
        # FOG w wersji polskiej: 0.4 * (srednia dlugosc zdania + % slow trudnych)
        report.fog = 0.4 * (asl + report.long_words_pct)
        # Indeks Pisarka (uproszczony, skala 1-20 lat nauki)
        report.pisarek = max(0.0, (asl + report.long_words_pct) / 3.0 - 1.0)
        # przelozenie FOG (lata nauki) na skale 0-100
        report.score = max(0.0, min(100.0, 100.0 - (report.fog - 4.0) * 6.0))

    report.level_key = _level_key(report.score)

    # --- spiewalnosc
    syl_report = analyze_syllables(text, lang)
    evenness = syl_report.evenness                          # 0-100
    avg_line = syl_report.average
    # optimum dla piosenki: 6-12 sylab w wersie
    if avg_line == 0:
        length_score = 0.0
    elif 6 <= avg_line <= 12:
        length_score = 100.0
    else:
        distance = 6 - avg_line if avg_line < 6 else avg_line - 12
        length_score = max(0.0, 100.0 - distance * 9.0)
    long_penalty = max(0.0, 100.0 - report.long_words_pct * 4.0)
    report.singability = round(0.4 * evenness + 0.4 * length_score + 0.2 * long_penalty, 1)

    # --- wersy trudne: duzo sylab lub duzo dlugich slow
    threshold = max(14, avg_line * 1.6)
    for number, raw in content_lines(text):
        line_syl = sum(count_syllables_word(w, lang) for w in WORD_RE.findall(raw))
        if line_syl > threshold:
            report.hard_lines.append((number, raw.strip(), line_syl))

    return report
