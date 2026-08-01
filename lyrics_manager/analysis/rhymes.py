"""Analiza rymow: schemat, jakosc, rymy wewnetrzne, wyszukiwanie rymow."""

from __future__ import annotations

import string
from dataclasses import dataclass, field

from .phonetics import is_vowel, rhyme_keys, tail_key
from .syllables import count_syllables_word
from .text_utils import WORD_RE, content_lines

# jakosc rymu, od najlepszej
QUALITY_IDENTITY = "identity"
QUALITY_PERFECT = "perfect"
QUALITY_SLANT = "slant"
QUALITY_ASSONANCE = "assonance"
QUALITY_NONE = "none"

_QUALITY_ORDER = {
    QUALITY_IDENTITY: 4,
    QUALITY_PERFECT: 3,
    QUALITY_SLANT: 2,
    QUALITY_ASSONANCE: 1,
    QUALITY_NONE: 0,
}


def compare_words(a: str, b: str, lang: str) -> str:
    """Okresla typ rymu miedzy dwoma wyrazami."""
    wa, wb = a.lower(), b.lower()
    if not wa or not wb:
        return QUALITY_NONE
    if wa == wb:
        return QUALITY_IDENTITY

    ka, va = rhyme_keys(wa, lang)
    kb, vb = rhyme_keys(wb, lang)
    if not ka or not kb:
        return QUALITY_NONE

    if ka == kb:
        return QUALITY_PERFECT

    # klucze tej samej dlugosci, te same samogloski, roznica w jednej
    # spolglosce - klasyczny rym niedokladny ("serce" / "wierzce")
    # Wymagamy klucza dlugosci >= 3, inaczej regula obejmowalaby wszystkie
    # jednosylabowce o wspolnej samoglosce ("kot" / "stol"), a to za malo.
    if len(ka) == len(kb) >= 3 and va == vb and va:
        diff = sum(1 for x, y in zip(ka, kb) if x != y)
        if diff == 1:
            return QUALITY_SLANT

    ta, tb = tail_key(wa, lang), tail_key(wb, lang)
    if ta == tb and len(ta) >= 2:
        return QUALITY_PERFECT
    if ta == tb:
        # zgadza sie tylko koncowa samogloska - to asonans, nie rym
        return QUALITY_ASSONANCE

    # ta sama koncowka spolgloskowa + zblizone samogloski
    if len(ta) >= 2 and len(tb) >= 2 and ta[-2:] == tb[-2:]:
        return QUALITY_SLANT

    # Wspolna koncowa spolgloska liczy sie jako rym niedokladny tylko wtedy,
    # gdy zgadza sie tez samogloska rdzenia. Sama koncowa samogloska
    # (np. "droga" / "trzyma") to najwyzej asonans, nie rym.
    ends_with_consonant = bool(ta) and not is_vowel(ta[-1], lang)
    if ends_with_consonant and ta[-1] == tb[-1:] and va[-1:] == vb[-1:]:
        return QUALITY_SLANT

    if va and vb and va == vb and len(va) >= 2:
        return QUALITY_ASSONANCE
    if va[-1:] and va[-1:] == vb[-1:] and ta[-1:] == tb[-1:]:
        return QUALITY_ASSONANCE
    return QUALITY_NONE


def rhymes(a: str, b: str, lang: str, min_quality: str = QUALITY_SLANT) -> bool:
    q = compare_words(a, b, lang)
    return _QUALITY_ORDER[q] >= _QUALITY_ORDER[min_quality] and q != QUALITY_IDENTITY


def last_word(line: str) -> str:
    found = WORD_RE.findall(line)
    return found[-1] if found else ""


@dataclass
class RhymeLine:
    number: int
    text: str
    word: str
    letter: str = "-"
    quality: str = QUALITY_NONE
    partners: list[int] = field(default_factory=list)
    syllables: int = 0


@dataclass
class InternalRhyme:
    line: int
    word_a: str
    word_b: str
    quality: str


@dataclass
class RhymeGroup:
    letter: str
    words: list[str]
    lines: list[int]
    quality: str


@dataclass
class RhymeReport:
    lines: list[RhymeLine] = field(default_factory=list)
    groups: list[RhymeGroup] = field(default_factory=list)
    internal: list[InternalRhyme] = field(default_factory=list)
    scheme: str = ""
    density: float = 0.0        # % wersow objetych rymem
    perfect_count: int = 0
    slant_count: int = 0
    unrhymed: list[int] = field(default_factory=list)


def _letters():
    for ch in string.ascii_uppercase:
        yield ch
    for first in string.ascii_uppercase:
        for second in string.ascii_uppercase:
            yield first + second


def analyze_rhymes(text: str, lang: str = "pl", window: int = 6) -> RhymeReport:
    """Analizuje rymy koncowe. `window` = ile wersow wstecz szukamy partnera."""
    report = RhymeReport()
    entries = [
        RhymeLine(number=n, text=t, word=last_word(t), syllables=count_syllables_word(last_word(t), lang))
        for n, t in content_lines(text)
    ]
    report.lines = entries

    letter_gen = _letters()
    assigned: dict[int, str] = {}
    group_map: dict[str, RhymeGroup] = {}

    for i, entry in enumerate(entries):
        if not entry.word:
            continue
        best_idx = -1
        best_quality = QUALITY_NONE
        for j in range(max(0, i - window), i):
            other = entries[j]
            if not other.word:
                continue
            q = compare_words(entry.word, other.word, lang)
            if q == QUALITY_IDENTITY:
                q = QUALITY_PERFECT if entry.word.lower() != other.word.lower() else QUALITY_IDENTITY
            if _QUALITY_ORDER[q] > _QUALITY_ORDER[best_quality]:
                best_quality, best_idx = q, j
            elif _QUALITY_ORDER[q] == _QUALITY_ORDER[best_quality] and q != QUALITY_NONE:
                best_idx = j  # preferuj blizszy wers

        if best_idx >= 0 and _QUALITY_ORDER[best_quality] >= _QUALITY_ORDER[QUALITY_ASSONANCE]:
            letter = assigned.get(best_idx)
            if letter is None:
                letter = next(letter_gen)
                assigned[best_idx] = letter
                entries[best_idx].letter = letter
                group_map[letter] = RhymeGroup(
                    letter=letter, words=[entries[best_idx].word],
                    lines=[entries[best_idx].number], quality=best_quality,
                )
            assigned[i] = letter
            entry.letter = letter
            entry.quality = best_quality
            entry.partners.append(entries[best_idx].number)
            entries[best_idx].partners.append(entry.number)
            grp = group_map[letter]
            grp.words.append(entry.word)
            grp.lines.append(entry.number)
            if _QUALITY_ORDER[best_quality] < _QUALITY_ORDER[grp.quality]:
                grp.quality = best_quality
            if best_quality == QUALITY_PERFECT or best_quality == QUALITY_IDENTITY:
                report.perfect_count += 1
            else:
                report.slant_count += 1

    for entry in entries:
        if entry.letter == "-":
            report.unrhymed.append(entry.number)

    report.scheme = "".join(e.letter if e.letter != "-" else "x" for e in entries)
    report.groups = [g for g in group_map.values() if len(g.lines) > 1]
    rhymed = sum(1 for e in entries if e.letter != "-")
    report.density = (100.0 * rhymed / len(entries)) if entries else 0.0
    report.internal = _internal_rhymes(entries, lang)
    return report


def _internal_rhymes(entries: list[RhymeLine], lang: str) -> list[InternalRhyme]:
    out: list[InternalRhyme] = []
    for entry in entries:
        ws = [w for w in WORD_RE.findall(entry.text) if len(w) > 2]
        for a in range(len(ws)):
            for b in range(a + 1, len(ws)):
                if ws[a].lower() == ws[b].lower():
                    continue
                q = compare_words(ws[a], ws[b], lang)
                if _QUALITY_ORDER[q] >= _QUALITY_ORDER[QUALITY_PERFECT]:
                    out.append(InternalRhyme(entry.number, ws[a], ws[b], q))
    return out


# --- wyszukiwarka rymow --------------------------------------------------

COMMON_PL = """
serce slonce noc dzien milosc wolnosc droga rzeka niebo ziemia wiatr deszcz ogien woda
cisza burza swiat czas krew sen mysl usta oczy dlonie ramiona kroki slowa piesn glos
sciana okno drzwi miasto dom pokoj lustro cien swiatlo mrok gwiazdy ksiezyc morze brzeg
poranek wieczor zima wiosna lato jesien pamiec obietnica nadzieja strach odwaga wina
imie twarz serca drzewo kwiat lisc korzen popiol iskra plomien blizna rana lek spokoj
zycie smierc anioł diabel raj pieklo modlitwa grzech wybaczenie powrot ucieczka podroz
biegne place smieje kocham wolam czekam wracam odchodze pamietam zapominam wierze marze
tancze spiewam milcze krzycze szukam znajduje trace zostaje ide stoje padam wstaje
jasno ciemno cicho glosno blisko daleko wczoraj jutro zawsze nigdy znowu jeszcze
gorzki slodki zimny cieply pusty pelny cichy dziki wolny smutny szczesliwy zmeczony
"""

COMMON_EN = """
heart night day light love free road river sky earth wind rain fire water silence storm
world time blood dream mind lips eyes hands arms steps words song voice wall window door
city home room mirror shadow dark stars moon sea shore morning evening winter spring
summer fall memory promise hope fear courage blame name face tree flower leaf root ash
spark flame scar wound life death angel devil heaven hell prayer sin forgiveness return
escape journey run cry laugh love call wait come back remember forget believe dream
dance sing quiet scream search find lose stay go stand fall rise bright dim close far
yesterday tomorrow always never again still bitter sweet cold warm empty full wild lonely
happy tired broken golden silver burning falling holding waiting breaking turning
"""


def _builtin_pool(lang: str) -> list[str]:
    source = COMMON_PL if lang == "pl" else COMMON_EN
    return source.split()


@dataclass
class RhymeCandidate:
    word: str
    quality: str
    syllables: int
    source: str  # "text" | "dictionary"


def find_rhymes(
    word: str,
    lang: str = "pl",
    extra_pool: list[str] | None = None,
    limit: int = 60,
) -> list[RhymeCandidate]:
    """Szuka rymow w slowniku wbudowanym i w slowach przekazanych w `extra_pool`."""
    target = word.strip().lower()
    if not target:
        return []

    seen: set[str] = {target}
    results: list[RhymeCandidate] = []

    def scan(pool, source):
        for cand in pool:
            c = cand.strip(string.punctuation + "’'").lower()
            if not c or c in seen or len(c) < 2:
                continue
            q = compare_words(target, c, lang)
            if _QUALITY_ORDER[q] >= _QUALITY_ORDER[QUALITY_ASSONANCE] and q != QUALITY_IDENTITY:
                seen.add(c)
                results.append(RhymeCandidate(c, q, count_syllables_word(c, lang), source))

    if extra_pool:
        scan(extra_pool, "text")
    scan(_builtin_pool(lang), "dictionary")

    results.sort(key=lambda r: (-_QUALITY_ORDER[r.quality], r.syllables, r.word))
    return results[:limit]


def words_from_text(text: str) -> list[str]:
    return WORD_RE.findall(text)
