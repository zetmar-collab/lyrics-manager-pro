"""Licznik sylab dla jezyka polskiego i angielskiego.

Polski liczymy niemal deterministycznie (sylaba = grupa samoglosek, z regula
o zmiekczajacym "i"), angielski heurystycznie z lista wyjatkow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text_utils import WORD_RE, content_lines, is_section_marker, section_name

PL_VOWELS = set("aeiouyąęó")
EN_VOWELS = set("aeiouy")

# "i" przed samogloska zmiekcza spolgloske i nie tworzy wlasnej sylaby:
# "kia" = 1, "ziemia" = 2, "ciasto" = 2.
_PL_SOFT_I = re.compile(r"(?<=[bcdfghjklmnprstwzżźśńćłq])i(?=[aeouyąęó])")

# Angielskie wyjatki, ktore heurystyka liczy zle.
EN_EXCEPTIONS = {
    "the": 1, "a": 1, "i": 1, "every": 3, "everyone": 3, "everything": 3, "everybody": 4,
    "business": 2, "beautiful": 3, "people": 2, "little": 2, "simile": 3, "orange": 2,
    "fire": 1, "hour": 1, "our": 1, "hire": 1, "tired": 1, "wire": 1, "choir": 1,
    "quiet": 2, "poem": 2, "poet": 2, "science": 2, "being": 2, "doing": 2, "going": 2,
    "area": 3, "idea": 3, "real": 1, "really": 2, "cruel": 2, "create": 2, "created": 3,
    "one": 1, "once": 1, "some": 1, "come": 1, "gone": 1, "done": 1, "love": 1, "have": 1,
    "give": 1, "live": 1, "were": 1, "where": 1, "there": 1, "here": 1, "more": 1,
    "heaven": 2, "seven": 2, "eleven": 3, "rhythm": 2, "prism": 2, "chasm": 2,
    "aisle": 1, "isle": 1, "queue": 1, "eye": 1, "lie": 1, "die": 1, "pie": 1, "tie": 1,
    "shoes": 1, "does": 1, "goes": 1, "toes": 1, "iron": 2, "lion": 2, "million": 3,
}

# Koncowki, po ktorych "-ed" NIE tworzy sylaby (walked = 1, ale wanted = 2).
_ED_SYLLABIC = re.compile(r"[td]ed$")
_ES_SYLLABIC = re.compile(r"(?:[sxz]|ch|sh|ge|ce|se)es$")


def count_syllables_pl(word: str) -> int:
    w = word.lower()
    w = _PL_SOFT_I.sub("", w)
    count = 0
    prev_vowel = False
    for ch in w:
        vowel = ch in PL_VOWELS
        if vowel and not prev_vowel:
            count += 1
        prev_vowel = vowel
    # "au"/"eu" w zapozyczeniach (Europa, auto) bywaja dwuglaskami - grupa
    # samoglosek liczona jako 1 jest tu wystarczajacym przyblizeniem.
    return max(count, 1) if any(c.isalpha() for c in w) else 0


def count_syllables_en(word: str) -> int:
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return 0
    if w in EN_EXCEPTIONS:
        return EN_EXCEPTIONS[w]

    stem = w
    extra = 0

    # koncowka -es / -ed
    if stem.endswith("es") and len(stem) > 3:
        if _ES_SYLLABIC.search(stem):
            extra += 1
        stem = stem[:-2]
    elif stem.endswith("ed") and len(stem) > 3:
        if _ED_SYLLABIC.search(stem):
            extra += 1
        stem = stem[:-2]

    # nieme koncowe "e" (ale nie w "-le" po spolglosce: table, little)
    if stem.endswith("e") and len(stem) > 2 and not stem.endswith(("le", "ee", "ye", "oe")):
        stem = stem[:-1]
    elif stem.endswith("le") and len(stem) > 2 and stem[-3] not in EN_VOWELS:
        pass  # "-ble", "-tle" tworza sylabe - zostawiamy

    count = 0
    prev_vowel = False
    for ch in stem:
        vowel = ch in EN_VOWELS
        if vowel and not prev_vowel:
            count += 1
        prev_vowel = vowel

    # koncowe "y" jako samogloska juz policzone powyzej
    total = count + extra
    return max(total, 1)


def count_syllables_word(word: str, lang: str = "pl") -> int:
    return count_syllables_pl(word) if lang == "pl" else count_syllables_en(word)


def count_syllables_line(line: str, lang: str = "pl") -> int:
    if is_section_marker(line):
        return 0
    return sum(count_syllables_word(w, lang) for w in WORD_RE.findall(line))


def count_syllables_text(text: str, lang: str = "pl") -> int:
    return sum(count_syllables_line(ln, lang) for ln in text.splitlines())


@dataclass
class LineStat:
    number: int          # numer wersu w calym tekscie (1-based)
    text: str
    syllables: int
    words: int
    chars: int
    section: str | None = None


@dataclass
class SectionStat:
    name: str
    start_line: int
    lines: int = 0
    syllables: int = 0


@dataclass
class SyllableReport:
    lines: list[LineStat] = field(default_factory=list)
    sections: list[SectionStat] = field(default_factory=list)
    total_lines: int = 0
    total_syllables: int = 0
    total_words: int = 0
    total_chars: int = 0
    average: float = 0.0
    minimum: int = 0
    maximum: int = 0
    evenness: float = 0.0        # 0-100, im wyzej tym rowniejsze wersy
    histogram: list[tuple[int, int]] = field(default_factory=list)


def analyze_syllables(text: str, lang: str = "pl") -> SyllableReport:
    report = SyllableReport()
    current_section: SectionStat | None = None

    for idx, raw in enumerate(text.splitlines(), start=1):
        if is_section_marker(raw):
            current_section = SectionStat(name=section_name(raw) or "", start_line=idx)
            report.sections.append(current_section)
            continue
        if not raw.strip():
            continue
        syl = count_syllables_line(raw, lang)
        wcount = len(WORD_RE.findall(raw))
        stat = LineStat(
            number=idx,
            text=raw,
            syllables=syl,
            words=wcount,
            chars=len(raw.strip()),
            section=current_section.name if current_section else None,
        )
        report.lines.append(stat)
        if current_section:
            current_section.lines += 1
            current_section.syllables += syl

    counts = [ln.syllables for ln in report.lines]
    report.total_lines = len(counts)
    report.total_syllables = sum(counts)
    report.total_words = sum(ln.words for ln in report.lines)
    report.total_chars = sum(ln.chars for ln in report.lines)

    if counts:
        report.average = report.total_syllables / len(counts)
        report.minimum = min(counts)
        report.maximum = max(counts)
        mean = report.average
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)
        std = variance ** 0.5
        # wspolczynnik zmiennosci -> 0-100 (100 = wszystkie wersy rowne)
        cv = (std / mean) if mean else 0.0
        report.evenness = max(0.0, min(100.0, 100.0 * (1.0 - cv)))
        hist: dict[int, int] = {}
        for c in counts:
            hist[c] = hist.get(c, 0) + 1
        report.histogram = sorted(hist.items())

    return report


def syllable_gutter(text: str, lang: str = "pl") -> list[str]:
    """Zwraca liste etykiet do rynny edytora - po jednej na wers."""
    out: list[str] = []
    for raw in text.splitlines():
        if is_section_marker(raw):
            out.append("§")
        elif not raw.strip():
            out.append("")
        else:
            out.append(str(count_syllables_line(raw, lang)))
    return out
