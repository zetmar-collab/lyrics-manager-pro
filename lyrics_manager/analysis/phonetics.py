"""Uproszczona transkrypcja fonetyczna dla polskiego i angielskiego.

Nie jest to pelny transkryptor IPA - celem jest stabilny klucz, ktory pozwala
porownywac zakonczenia wyrazow tak, jak slyszy je ucho.
"""

from __future__ import annotations

import re

# --- POLSKI --------------------------------------------------------------

PL_VOWEL_PHONEMES = set("aeiouyAE")  # A = ą, E = ę (nosowki)

_PL_DIGRAPHS = [
    ("dzi", "J"),   # dź
    ("dz", "3"),
    ("dż", "D"),
    ("drz", "D"),
    ("dź", "J"),
    ("cz", "C"),
    ("trz", "C"),
    ("sz", "S"),
    ("rz", "Z"),
    ("ż", "Z"),
    ("ź", "Zj"),
    ("zi", "Zj"),
    ("ś", "Sj"),
    ("si", "Sj"),
    ("ć", "Cj"),
    ("ci", "Cj"),
    ("ń", "nj"),
    ("ni", "nj"),
    ("ch", "h"),
    ("ł", "w"),
    ("ó", "u"),
    ("ą", "A"),
    ("ę", "E"),
    ("ć", "Cj"),
]

# ubezdzwiecznienie w wyglosie
_PL_FINAL_DEVOICE = {
    "b": "p", "d": "t", "g": "k", "w": "f", "z": "s",
    "Z": "S", "3": "c", "D": "C", "J": "Cj", "Zj": "Sj",
}


def pl_phonetic(word: str) -> str:
    w = word.lower().strip("'’-")
    # digrafy - kolejnosc ma znaczenie (najdluzsze najpierw)
    for src, dst in sorted(_PL_DIGRAPHS, key=lambda x: -len(x[0])):
        w = w.replace(src, dst)
    w = w.replace("v", "w").replace("q", "k").replace("x", "ks")
    # "i" miedzy spolgloska a samogloska tylko zmiekcza - nie jest osobna
    # samogloska ("miasta" brzmi jak "mjasta"). Bez tego rymy typu
    # "miasta / ciasta" wypadaja poza klucz rymowy.
    w = re.sub(r"(?<=[bcdfghjklmnprstwzCSZD3])i(?=[aeouyAE])", "j", w)
    # uproszczenie podwojnych spolglosek
    w = re.sub(r"(.)\1+", r"\1", w)
    # ubezdzwiecznienie ostatniej spolgloski
    for src, dst in sorted(_PL_FINAL_DEVOICE.items(), key=lambda x: -len(x[0])):
        if w.endswith(src):
            w = w[: -len(src)] + dst
            break
    return w


def pl_is_vowel(ch: str) -> bool:
    return ch in PL_VOWEL_PHONEMES


# --- ANGIELSKI -----------------------------------------------------------

EN_VOWEL_PHONEMES = set("aeiouy")

_EN_RULES: list[tuple[str, str]] = [
    (r"ough$", "o"),
    (r"augh", "af"),
    (r"tion", "Sn"),
    (r"sion", "Sn"),
    (r"cious", "Ss"),
    (r"tious", "Ss"),
    (r"ph", "f"),
    (r"^wr", "r"),
    (r"^rh", "r"),
    (r"^kn", "n"),
    (r"^gn", "n"),
    (r"^ps", "s"),
    (r"gh$", ""),
    (r"ght", "t"),
    (r"ck", "k"),
    (r"qu", "kw"),
    (r"x", "ks"),
    (r"sh", "S"),
    (r"ch", "C"),
    (r"th", "T"),
    (r"c(?=[eiy])", "s"),
    (r"c", "k"),
    (r"wh", "w"),
    (r"ng$", "N"),
]


def en_phonetic(word: str) -> str:
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return ""
    for pattern, repl in _EN_RULES:
        w = re.sub(pattern, repl, w)
    # nieme koncowe "e"
    if len(w) > 2 and w.endswith("e") and w[-2] not in EN_VOWEL_PHONEMES:
        w = w[:-1]
    # "y" poza nagloskiem jest samogloska: "rhyme" -> "rime", "sky" -> "ski"
    w = re.sub(r"(?<=.)y", "i", w)
    w = re.sub(r"(.)\1+", r"\1", w)
    return w


def en_is_vowel(ch: str) -> bool:
    return ch in EN_VOWEL_PHONEMES


# --- wspolne -------------------------------------------------------------

def phonetic(word: str, lang: str) -> str:
    return pl_phonetic(word) if lang == "pl" else en_phonetic(word)


def is_vowel(ch: str, lang: str) -> bool:
    return pl_is_vowel(ch) if lang == "pl" else en_is_vowel(ch)


def vowel_positions(phon: str, lang: str) -> list[int]:
    """Pozycje poczatkow grup samogloskowych."""
    out: list[int] = []
    prev = False
    for i, ch in enumerate(phon):
        v = is_vowel(ch, lang)
        if v and not prev:
            out.append(i)
        prev = v
    return out


def rhyme_keys(word: str, lang: str) -> tuple[str, str]:
    """Zwraca (klucz_rymu, klucz_samogloskowy).

    Klucz rymu to fragment od samogloski akcentowanej do konca wyrazu:
    - polski: akcent na przedostatniej sylabie,
    - angielski: przyblizamy ostatnia samogloska (dla wyrazow 1-2 sylabowych
      to zwykle sylaba akcentowana).
    Klucz samogloskowy to same samogloski z tego fragmentu (asonans).
    """
    phon = phonetic(word, lang)
    if not phon:
        return "", ""
    positions = vowel_positions(phon, lang)
    if not positions:
        return phon, ""

    if lang == "pl":
        idx = positions[-2] if len(positions) >= 2 else positions[-1]
    else:
        # dla dluzszych slow bierzemy przedostatnia samogloske, zeby zlapac
        # rymy zenskie typu "burning / turning"
        idx = positions[-2] if len(positions) >= 3 else positions[-1]

    key = phon[idx:]
    vkey = "".join(ch for ch in key if is_vowel(ch, lang))
    return key, vkey


def tail_key(word: str, lang: str) -> str:
    """Klucz od ostatniej samogloski - rym meski / jednosylabowy."""
    phon = phonetic(word, lang)
    positions = vowel_positions(phon, lang)
    if not positions:
        return phon
    return phon[positions[-1]:]
