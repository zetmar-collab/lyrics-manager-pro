"""Budowanie promptow dla zadan autora tekstow.

Jezyk odpowiedzi (`out_lang`) jest niezalezny od jezyka interfejsu i od jezyka
analizowanego tekstu - autor moze pisac po polsku i prosic o komentarz po
angielsku albo odwrotnie.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ChatMessage

TASKS = [
    "alternatives", "rhymes", "continue", "polish", "metaphors",
    "simplify", "fit_syllables", "translate", "title", "critique", "suno_prompt",
]

TASK_LABEL_KEYS = {t: f"task.{t}" for t in TASKS}

_LANG_NAME = {"pl": "polskim", "en": "angielskim"}
_LANG_NAME_EN = {"pl": "Polish", "en": "English"}

_SYSTEM_PL = """Jesteś doświadczonym autorem tekstów piosenek i redaktorem.
Znasz się na metryce, akcentach, rymach dokładnych i niedokładnych, frazowaniu
i na tym, jak tekst układa się w ustach wokalisty.

Zasady:
- Odpowiadasz wyłącznie w języku {out_lang_pl}, z pełną polską interpunkcją
  i znakami diakrytycznymi.
- Piszesz żywym, naturalnym językiem, bez kalek językowych i bez waty słownej.
- Szanujesz zamysł autora: nie zmieniasz tematu ani nastroju, o ile nie poproszono.
- Podajesz konkret, nie ogólniki. Żadnych wstępów typu "Oto propozycje".
- Nie dodajesz komentarzy o sobie ani o tym, że jesteś modelem językowym.
- Formatujesz odpowiedź zwięźle, używając prostych nagłówków i list."""

_SYSTEM_EN = """You are an experienced songwriter and lyric editor.
You know meter, stress placement, perfect and slant rhyme, phrasing, and how a
line actually sits in a singer's mouth.

Rules:
- Answer only in {out_lang_en}.
- Write in living, natural language - no filler, no translationese.
- Respect the author's intent: do not change topic or mood unless asked.
- Be concrete. No preambles like "Here are some suggestions".
- Never comment on yourself or on being a language model.
- Keep the formatting tight: simple headings and lists."""


@dataclass
class PromptContext:
    task: str
    text: str                 # fragment do obrobki
    full_text: str = ""       # caly utwor (kontekst)
    text_lang: str = "pl"     # jezyk tekstu piosenki
    out_lang: str = "pl"      # jezyk odpowiedzi AI
    extra: str = ""           # dodatkowe wskazowki uzytkownika
    title: str = ""
    artist: str = ""
    style: str = ""
    syllables_per_line: list[int] | None = None
    rhyme_scheme: str = ""
    target_word: str = ""     # dla zadania "rhymes"


def system_prompt(ctx: PromptContext) -> str:
    if ctx.out_lang == "pl":
        return _SYSTEM_PL.format(out_lang_pl=_LANG_NAME["pl"])
    return _SYSTEM_EN.format(out_lang_en=_LANG_NAME_EN["en"])


_INSTRUCTIONS: dict[str, dict[str, str]] = {
    "alternatives": {
        "pl": (
            "Zaproponuj 4 alternatywne wersje poniższego fragmentu. Każda ma mieć inny "
            "charakter: (1) bliżej oryginału, tylko lepiej dobrane słowa, (2) bardziej "
            "obrazowa, (3) prostsza i mocniejsza rytmicznie, (4) odważna, zaskakująca. "
            "Zachowaj liczbę wersów i, w miarę możliwości, liczbę sylab. Ponumeruj wersje "
            "i pod każdą dodaj jedno zdanie: co się zmieniło i po co."
        ),
        "en": (
            "Give 4 alternative versions of the passage below. Each with a different angle: "
            "(1) close to the original, just better word choices, (2) more image-driven, "
            "(3) simpler and rhythmically stronger, (4) bold and surprising. Keep the line "
            "count and, where possible, the syllable count. Number the versions and add one "
            "sentence under each: what changed and why."
        ),
    },
    "rhymes": {
        "pl": (
            "Podaj rymy do słowa podanego niżej. Pogrupuj je: rymy dokładne, rymy "
            "niedokładne i asonanse oraz rymy składane (wielowyrazowe). Przy każdym podaj "
            "liczbę sylab. Odrzuć banalne rymy gramatyczne (samo -ać, -enie, -ami). "
            "Na końcu daj 3 gotowe wersy z najlepszymi z tych rymów, pasujące do utworu."
        ),
        "en": (
            "List rhymes for the word given below. Group them: perfect rhymes, slant rhymes / "
            "assonances, and multi-word (compound) rhymes. Give the syllable count for each. "
            "Skip trivial grammatical rhymes. Finally, write 3 ready-made lines using the best "
            "of those rhymes, fitting the song's context."
        ),
    },
    "continue": {
        "pl": (
            "Dopisz dalszy ciąg tekstu, około 8 wersów. Utrzymaj tego samego narratora, nastrój, "
            "długość wersów i schemat rymów co w materiale wyjściowym. Nie powtarzaj tego, "
            "co już jest. Sam tekst, bez komentarza."
        ),
        "en": (
            "Continue the lyrics - about 8 lines. Keep the same narrator, mood, line length "
            "and rhyme scheme as the source. Do not repeat what is already there. "
            "Lyrics only, no commentary."
        ),
    },
    "polish": {
        "pl": (
            "Dopracuj język fragmentu: usuń watę słowną, wyrzuć słowa-wypełniacze, popraw "
            "szyk i akcenty tak, żeby wersy lepiej się śpiewały. Nie zmieniaj sensu ani "
            "liczby wersów. Podaj poprawioną wersję, a pod nią krótką listę najważniejszych zmian."
        ),
        "en": (
            "Polish the passage: cut filler, fix word order and stress so the lines sing "
            "better. Do not change the meaning or the number of lines. Give the revised "
            "version, then a short list of the key changes."
        ),
    },
    "metaphors": {
        "pl": (
            "Wzmocnij obrazowanie fragmentu. Zamień abstrakcje na konkret zmysłowy "
            "(wzrok, dotyk, dźwięk, zapach). Unikaj zużytych metafor. Podaj poprawioną "
            "wersję oraz 5 alternatywnych obrazów do wykorzystania w dalszej części utworu."
        ),
        "en": (
            "Strengthen the imagery. Replace abstractions with concrete sensory detail "
            "(sight, touch, sound, smell). Avoid worn-out metaphors. Give the revised version "
            "plus 5 alternative images usable later in the song."
        ),
    },
    "simplify": {
        "pl": (
            "Uprość fragment: krótsze słowa, krótsze wersy, mniej zdań podrzędnych. Ma być "
            "łatwiej zapamiętać i zaśpiewać, ale sens musi zostać. Podaj wersję uproszczoną "
            "i zaznacz, ile sylab ma teraz każdy wers."
        ),
        "en": (
            "Simplify the passage: shorter words, shorter lines, fewer subordinate clauses. "
            "It must be easier to remember and sing while keeping the meaning. Give the "
            "simplified version and mark the syllable count of each line."
        ),
    },
    "fit_syllables": {
        "pl": (
            "Przepisz fragment tak, żeby każdy wers miał docelową liczbę sylab podaną we "
            "wskazówkach (jeśli jej nie podano, wyrównaj wersy do długości najczęstszej "
            "w tym fragmencie). Sens i rymy mają zostać. Po każdym wersie podaj w nawiasie "
            "liczbę sylab."
        ),
        "en": (
            "Rewrite the passage so every line has the target syllable count given in the "
            "instructions (if none is given, level the lines to the most common length in "
            "the passage). Keep meaning and rhymes. Put the syllable count in brackets "
            "after each line."
        ),
    },
    "translate": {
        "pl": (
            "Przetłumacz fragment tak, żeby dało się go zaśpiewać: zachowaj liczbę sylab, "
            "miejsca akcentów i schemat rymów. To ma być przekład piosenki, nie dosłowny. "
            "Podaj tłumaczenie, a pod nim krótką notkę o miejscach, w których trzeba było "
            "odejść od dosłowności."
        ),
        "en": (
            "Translate the passage so it can actually be sung: keep the syllable count, "
            "stress placement and rhyme scheme. This is a singable translation, not a literal "
            "one. Give the translation, then a short note on where you had to depart from "
            "the literal meaning."
        ),
    },
    "title": {
        "pl": (
            "Zaproponuj 10 tytułów dla tego utworu. Pomieszaj rejestry: dosadne, poetyckie, "
            "wzięte wprost z tekstu oraz takie, których w tekście nie ma. Przy każdym jedno "
            "zdanie uzasadnienia."
        ),
        "en": (
            "Suggest 10 titles for this song. Mix registers: blunt, poetic, lifted straight "
            "from the lyrics, and ones that do not appear in the text at all. One sentence "
            "of reasoning for each."
        ),
    },
    "critique": {
        "pl": (
            "Zrecenzuj ten tekst jak redaktor wydawnictwa muzycznego. Omów: (1) pomysł i "
            "spójność, (2) obrazowanie i język, (3) metrykę i rymy, (4) refren, czy się "
            "wybija, (5) trzy najważniejsze rzeczy do poprawy, konkretnie, z przykładami z "
            "tekstu. Bądź szczery, nie pochlebiaj."
        ),
        "en": (
            "Critique these lyrics like a music publisher's editor. Cover: (1) concept and "
            "coherence, (2) imagery and language, (3) meter and rhyme, (4) does the chorus "
            "land, (5) the three most important fixes, concretely, quoting the text. "
            "Be honest, do not flatter."
        ),
    },
    "suno_prompt": {
        "pl": (
            "Na podstawie tekstu zbuduj opis stylu (style prompt) dla generatora muzyki "
            "AI, np. Suno lub Udio. Podaj: (1) jedną linijkę stylu do pola 'Style of Music' "
            "gatunek, instrumentarium, tempo, nastrój, typ wokalu, do 200 znaków; "
            "(2) 3 warianty alternatywne; (3) listę tagów negatywnych: czego unikać."
        ),
        "en": (
            "From these lyrics build a style prompt for an AI music generator such as Suno "
            "or Udio. Give: (1) one line for the 'Style of Music' field - genre, "
            "instrumentation, tempo, mood, vocal type, up to 200 characters; (2) 3 alternative "
            "variants; (3) a list of negative tags, what to avoid."
        ),
    },
}


def _label(pl: str, en: str, lang: str) -> str:
    return pl if lang == "pl" else en


def build_messages(ctx: PromptContext) -> list[ChatMessage]:
    lang = ctx.out_lang
    instruction = _INSTRUCTIONS.get(ctx.task, _INSTRUCTIONS["alternatives"])[lang]

    parts: list[str] = [instruction]

    meta: list[str] = []
    if ctx.title:
        meta.append(f"{_label('Tytuł', 'Title', lang)}: {ctx.title}")
    if ctx.artist:
        meta.append(f"{_label('Wykonawca', 'Artist', lang)}: {ctx.artist}")
    if ctx.style:
        meta.append(f"{_label('Styl', 'Style', lang)}: {ctx.style}")
    meta.append(
        f"{_label('Język tekstu piosenki', 'Language of the lyrics', lang)}: "
        f"{_LANG_NAME_EN[ctx.text_lang]}"
    )
    if ctx.rhyme_scheme:
        meta.append(f"{_label('Wykryty schemat rymów', 'Detected rhyme scheme', lang)}: {ctx.rhyme_scheme}")
    if ctx.syllables_per_line:
        counts = ", ".join(str(c) for c in ctx.syllables_per_line[:40])
        meta.append(f"{_label('Sylaby w kolejnych wersach', 'Syllables per line', lang)}: {counts}")

    parts.append("\n".join(meta))

    if ctx.task == "rhymes" and ctx.target_word:
        parts.append(f"{_label('SŁOWO DO ORYMOWANIA', 'WORD TO RHYME', lang)}: {ctx.target_word}")

    if ctx.extra.strip():
        parts.append(
            f"{_label('DODATKOWE WSKAZÓWKI AUTORA', 'AUTHOR EXTRA INSTRUCTIONS', lang)}:\n"
            f"{ctx.extra.strip()}"
        )

    fragment_label = _label("FRAGMENT DO PRACY", "PASSAGE TO WORK ON", lang)
    parts.append(f"{fragment_label}:\n---\n{ctx.text.strip()}\n---")

    if ctx.full_text.strip() and ctx.full_text.strip() != ctx.text.strip():
        ctx_label = _label("CAŁY UTWÓR (kontekst)", "FULL SONG (context)", lang)
        full = ctx.full_text.strip()
        if len(full) > 8000:
            full = full[:8000] + "\n[...]"
        parts.append(f"{ctx_label}:\n---\n{full}\n---")

    if ctx.task in {"continue", "fit_syllables"}:
        parts.append(
            _label(
                "W odpowiedzi podaj sam tekst piosenki, gotowy do wklejenia.",
                "Reply with the lyrics only, ready to paste.",
                lang,
            )
        )

    return [
        ChatMessage("system", system_prompt(ctx)),
        ChatMessage("user", "\n\n".join(p for p in parts if p.strip())),
    ]
