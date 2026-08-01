"""Eksport tekstu do Suno, Udio, czystego tekstu i Markdown z analiza."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .analysis.readability import analyze_readability
from .analysis.repetition import analyze_repetition
from .analysis.rhymes import analyze_rhymes
from .analysis.syllables import analyze_syllables
from .analysis.text_utils import is_section_marker, section_name

# Limity pol w generatorach (stan na 2025; zapas bezpieczenstwa wliczony).
LIMITS = {
    "suno": {"lyrics": 5000, "style": 200},
    "udio": {"lyrics": 4000, "style": 250},
}

# Nazwy sekcji rozpoznawane przy normalizacji znacznikow.
_SECTION_ALIASES = {
    "intro": "Intro", "wstep": "Intro", "wstęp": "Intro",
    "zwrotka": "Verse", "verse": "Verse", "zwr": "Verse",
    "refren": "Chorus", "chorus": "Chorus", "ref": "Chorus",
    "przedrefren": "Pre-Chorus", "pre-chorus": "Pre-Chorus", "prechorus": "Pre-Chorus",
    "most": "Bridge", "bridge": "Bridge",
    "outro": "Outro", "zakonczenie": "Outro", "zakończenie": "Outro",
    "hook": "Hook", "post-chorus": "Post-Chorus", "postrefren": "Post-Chorus",
    "instrumental": "Instrumental", "solo": "Instrumental",
}

_NUM_RE = re.compile(r"(\d+)")


@dataclass
class SongMeta:
    title: str = ""
    artist: str = ""
    style: str = ""
    tempo: str = ""
    key: str = ""
    notes: str = ""


def normalize_section(name: str) -> str:
    """[Zwrotka 2] -> [Verse 2], [refren] -> [Chorus]."""
    raw = name.strip()
    number = ""
    m = _NUM_RE.search(raw)
    if m:
        number = f" {m.group(1)}"
    base = _NUM_RE.sub("", raw).strip(" :-").lower()
    mapped = _SECTION_ALIASES.get(base)
    if mapped:
        return f"{mapped}{number}"
    return raw


def _auto_tag(text: str) -> str:
    """Dokleja znaczniki sekcji, jesli autor ich nie uzyl.

    Blok oddzielony pusta linia -> kolejna zwrotka; blok powtorzony -> refren.
    """
    lines = text.splitlines()
    if any(is_section_marker(ln) for ln in lines):
        return text

    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line.rstrip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    if not blocks:
        return text

    fingerprints = [" ".join(b).lower() for b in blocks]
    repeated = {fp for fp in fingerprints if fingerprints.count(fp) > 1}

    out: list[str] = []
    verse_no = 0
    for block, fp in zip(blocks, fingerprints):
        if fp in repeated:
            out.append("[Chorus]")
        else:
            verse_no += 1
            out.append(f"[Verse {verse_no}]")
        out.extend(block)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _tagged_body(text: str, autotag: bool) -> str:
    body = _auto_tag(text) if autotag else text
    out: list[str] = []
    for line in body.splitlines():
        if is_section_marker(line):
            out.append(f"[{normalize_section(section_name(line) or '')}]")
        else:
            out.append(line.rstrip())
    # nie wiecej niz jedna pusta linia z rzedu
    cleaned: list[str] = []
    for line in out:
        if not line.strip() and cleaned and not cleaned[-1].strip():
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def build_style_prompt(meta: SongMeta, target: str) -> str:
    parts = [p.strip() for p in (meta.style, meta.tempo, meta.key) if p and p.strip()]
    if meta.tempo and meta.tempo.strip().isdigit():
        parts = [p if p != meta.tempo.strip() else f"{meta.tempo.strip()} BPM" for p in parts]
    line = ", ".join(parts)
    limit = LIMITS.get(target, {}).get("style", 200)
    return line[:limit]


def export_suno(text: str, meta: SongMeta, autotag: bool = True,
                include_meta: bool = True) -> str:
    body = _tagged_body(text, autotag)
    header: list[str] = []
    if include_meta:
        if meta.title:
            header.append(f"# {meta.title}")
        style = build_style_prompt(meta, "suno")
        if style:
            header.append(f"# Style of Music: {style}")
        if header:
            header.append("")
    return "\n".join(header) + body


def export_udio(text: str, meta: SongMeta, autotag: bool = True,
                include_meta: bool = True) -> str:
    body = _tagged_body(text, autotag)
    header: list[str] = []
    if include_meta:
        if meta.title:
            header.append(f"Title: {meta.title}")
        style = build_style_prompt(meta, "udio")
        if style:
            header.append(f"Prompt: {style}")
        if header:
            header.append("")
    return "\n".join(header) + body


def export_plain(text: str, meta: SongMeta, include_meta: bool = True) -> str:
    header: list[str] = []
    if include_meta:
        if meta.title:
            header.append(meta.title)
        if meta.artist:
            header.append(meta.artist)
        if header:
            header.append("")
    return "\n".join(header) + text.strip() + "\n"


def export_markdown(text: str, meta: SongMeta, text_lang: str = "pl") -> str:
    """Tekst wraz z pelnym raportem analitycznym."""
    syl = analyze_syllables(text, text_lang)
    rhy = analyze_rhymes(text, text_lang)
    rep = analyze_repetition(text, text_lang)
    rdb = analyze_readability(text, text_lang)

    lines: list[str] = []
    lines.append(f"# {meta.title or 'Untitled'}")
    if meta.artist:
        lines.append(f"**{meta.artist}**")
    details = [d for d in (meta.style, meta.tempo and f"{meta.tempo} BPM", meta.key) if d]
    if details:
        lines.append(" · ".join(details))
    lines.append("")
    lines.append("## Tekst / Lyrics")
    lines.append("")
    lines.append("```")
    for line in text.splitlines():
        if line.strip() and not is_section_marker(line):
            count = next(
                (s.syllables for s in syl.lines if s.text == line), None
            )
            lines.append(f"{count if count is not None else '':>3} | {line}")
        else:
            lines.append(f"    | {line}")
    lines.append("```")
    lines.append("")

    lines.append("## Metryka / Metrics")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Wersy / Lines | {syl.total_lines} |")
    lines.append(f"| Sylaby / Syllables | {syl.total_syllables} |")
    lines.append(f"| Srednio na wers / Avg per line | {syl.average:.1f} |")
    lines.append(f"| Min / Max | {syl.minimum} / {syl.maximum} |")
    lines.append(f"| Rownomiernosc / Evenness | {syl.evenness:.0f}% |")
    lines.append(f"| Slowa / Words | {syl.total_words} |")
    lines.append("")

    lines.append("## Rymy / Rhymes")
    lines.append("")
    lines.append(f"- Schemat / Scheme: `{rhy.scheme}`")
    lines.append(f"- Gestosc / Density: {rhy.density:.0f}%")
    lines.append(f"- Dokladne / Perfect: {rhy.perfect_count}, "
                 f"niedokladne / slant: {rhy.slant_count}")
    if rhy.groups:
        lines.append("")
        for g in rhy.groups:
            lines.append(f"  - **{g.letter}** ({g.quality}): {', '.join(g.words)}")
    lines.append("")

    lines.append("## Powtorzenia / Repetitions")
    lines.append("")
    if rep.words[:10]:
        for item in rep.words[:10]:
            lines.append(f"- `{item.value}` × {item.count} (wersy {item.lines})")
    else:
        lines.append("- brak / none")
    if rep.phrases[:10]:
        lines.append("")
        for item in rep.phrases[:10]:
            lines.append(f"- \"{item.value}\" × {item.count}")
    lines.append("")

    lines.append("## Czytelnosc / Readability")
    lines.append("")
    lines.append(f"- Wynik / Score: **{rdb.score:.0f}/100**")
    lines.append(f"- Spiewalnosc / Singability: **{rdb.singability:.0f}/100**")
    if text_lang == "en":
        lines.append(f"- Flesch Reading Ease: {rdb.flesch:.1f}")
        lines.append(f"- Flesch-Kincaid Grade: {rdb.flesch_kincaid:.1f}")
    else:
        lines.append(f"- FOG: {rdb.fog:.1f}")
        lines.append(f"- Pisarek: {rdb.pisarek:.1f}")
    lines.append(f"- Slowa dlugie / Long words: {rdb.long_words} ({rdb.long_words_pct:.1f}%)")
    lines.append(f"- Bogactwo slownictwa / Lexical diversity: {rep.diversity:.1f}%")
    lines.append("")

    if meta.notes.strip():
        lines.append("## Notatki / Notes")
        lines.append("")
        lines.append(meta.notes.strip())
        lines.append("")

    return "\n".join(lines)


def export_text(target: str, text: str, meta: SongMeta, *, autotag: bool = True,
                include_meta: bool = True, text_lang: str = "pl") -> str:
    if target == "suno":
        return export_suno(text, meta, autotag, include_meta)
    if target == "udio":
        return export_udio(text, meta, autotag, include_meta)
    if target == "markdown":
        return export_markdown(text, meta, text_lang)
    return export_plain(text, meta, include_meta)


def check_limit(target: str, content: str) -> tuple[bool, int]:
    limit = LIMITS.get(target, {}).get("lyrics", 0)
    if not limit:
        return True, 0
    return len(content) <= limit, limit
