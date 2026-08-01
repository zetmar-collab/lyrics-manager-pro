"""Testy modulow analitycznych. Uruchomienie: python -m tests.test_analysis"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyrics_manager.analysis.readability import analyze_readability
from lyrics_manager.analysis.repetition import analyze_repetition
from lyrics_manager.analysis.rhymes import (
    QUALITY_ASSONANCE, QUALITY_NONE, QUALITY_PERFECT, QUALITY_SLANT,
    analyze_rhymes, compare_words, find_rhymes,
)
from lyrics_manager.analysis.syllables import (
    analyze_syllables, count_syllables_en, count_syllables_pl, count_syllables_line,
)
from lyrics_manager.document import Document
from lyrics_manager.export import SongMeta, export_suno, export_udio, export_markdown

FAILURES: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f"{label}: oczekiwano {expected!r}, jest {actual!r}")


def check_true(label: str, condition: bool) -> None:
    if not condition:
        FAILURES.append(f"{label}: warunek nie zostal spelniony")


# --- sylaby polskie -------------------------------------------------------

PL_CASES = {
    "kot": 1, "domy": 2, "serce": 2, "milosc": 2, "miłość": 2,
    "ziemia": 2, "ciasto": 2, "kia": 1, "wolnosc": 2,
    "przyjaciel": 3, "niebo": 2, "kompozytor": 4, "aaa": 1,
    "ktory": 2, "który": 2, "sierpien": 2, "poranek": 3,
    "obietnica": 4, "wybaczenie": 4, "gwiazdy": 2,
}

for word, expected in PL_CASES.items():
    check(f"PL sylaby '{word}'", count_syllables_pl(word), expected)

# --- sylaby angielskie ----------------------------------------------------

EN_CASES = {
    "cat": 1, "water": 2, "beautiful": 3, "fire": 1, "table": 2,
    "walked": 1, "wanted": 2, "houses": 2, "the": 1, "rhythm": 2,
    "burning": 2, "everything": 3, "silence": 2, "little": 2,
    "remember": 3, "goes": 1, "lie": 1,
}

for word, expected in EN_CASES.items():
    check(f"EN sylaby '{word}'", count_syllables_en(word), expected)

check("wers PL", count_syllables_line("Nie ma juz nic", "pl"), 4)
check("znacznik sekcji", count_syllables_line("[Refren]", "pl"), 0)

# --- raport sylab ---------------------------------------------------------

SAMPLE_PL = """[Zwrotka 1]
Wracam do domu nocna droga
Swiatla miasta gasna z tylu
Nie ma juz nic co mnie tu trzyma
Tylko cien na mokrym pylu

[Refren]
Biegne przez deszcz
Biegne przez deszcz
Nie zatrzyma mnie nic
Biegne przez deszcz
"""

SAMPLE_EN = """[Verse 1]
I walk the road back home tonight
The city lights are fading slow
There's nothing left to hold me here
Just shadows on the road below

[Chorus]
I'm running through the rain
I'm running through the rain
And nothing holds me down
I'm running through the rain
"""

syl = analyze_syllables(SAMPLE_PL, "pl")
check("liczba wersow PL", syl.total_lines, 8)
check_true("sylaby PL > 0", syl.total_syllables > 40)
check("sekcje PL", len(syl.sections), 2)
check_true("rownomiernosc 0-100", 0 <= syl.evenness <= 100)

syl_en = analyze_syllables(SAMPLE_EN, "en")
check("liczba wersow EN", syl_en.total_lines, 8)

# --- rymy -----------------------------------------------------------------

RHYME_CASES = [
    # (a, b, jezyk, oczekiwana jakosc)
    ("kot", "plot", "pl", QUALITY_PERFECT),
    ("tylu", "pylu", "pl", QUALITY_PERFECT),
    ("droga", "noga", "pl", QUALITY_PERFECT),
    ("miasta", "ciasta", "pl", QUALITY_PERFECT),
    ("deszcz", "leszcz", "pl", QUALITY_PERFECT),
    ("mnie", "nie", "pl", QUALITY_PERFECT),
    ("domu", "komu", "pl", QUALITY_PERFECT),
    ("wolnosc", "milosc", "pl", QUALITY_PERFECT),
    ("serce", "wierzce", "pl", QUALITY_SLANT),
    ("droga", "trzyma", "pl", QUALITY_ASSONANCE),
    ("kot", "stol", "pl", QUALITY_NONE),
    ("noc", "dzien", "pl", QUALITY_NONE),
    ("night", "light", "en", QUALITY_PERFECT),
    ("rain", "pain", "en", QUALITY_PERFECT),
    ("burning", "turning", "en", QUALITY_PERFECT),
    ("slow", "below", "en", QUALITY_PERFECT),
    ("here", "there", "en", QUALITY_PERFECT),
    ("love", "above", "en", QUALITY_PERFECT),
    ("time", "rhyme", "en", QUALITY_PERFECT),
    ("sky", "high", "en", QUALITY_PERFECT),
    ("day", "way", "en", QUALITY_PERFECT),
    ("heart", "start", "en", QUALITY_SLANT),
    ("road", "home", "en", QUALITY_NONE),
    ("cat", "dog", "en", QUALITY_NONE),
]

for a, b, lang, expected in RHYME_CASES:
    check(f"rym {lang} {a}/{b}", compare_words(a, b, lang), expected)

rhy = analyze_rhymes(SAMPLE_PL, "pl")
check_true("wykryto rymy PL", len(rhy.groups) >= 1)
check_true("schemat PL ma dlugosc wersow", len(rhy.scheme) == 8)
check_true("gestosc 0-100", 0 <= rhy.density <= 100)

rhy_en = analyze_rhymes(SAMPLE_EN, "en")
check_true("wykryto rymy EN", len(rhy_en.groups) >= 1)

cands = find_rhymes("serce", "pl")
check_true("znaleziono rymy do 'serce'", len(cands) > 0)
cands_en = find_rhymes("night", "en")
check_true("znaleziono rymy do 'night'", len(cands_en) > 0)

# --- powtorzenia ----------------------------------------------------------

rep = analyze_repetition(SAMPLE_PL, "pl", min_count=2)
check_true("wykryto powtarzajacy sie wers", len(rep.lines) >= 1)
check_true("wykryto powtarzajaca sie fraze", len(rep.phrases) >= 1)
check_true("bogactwo slownictwa 0-100", 0 < rep.diversity <= 100)
words_found = {r.value for r in rep.words}
check_true("'biegne' rozpoznane jako powtorzenie", "biegne" in words_found)
check_true("stopwords pominiete", "nie" not in words_found)

# --- czytelnosc -----------------------------------------------------------

rdb = analyze_readability(SAMPLE_PL, "pl")
check_true("wynik PL 0-100", 0 <= rdb.score <= 100)
check_true("spiewalnosc PL 0-100", 0 <= rdb.singability <= 100)
check_true("FOG policzony", rdb.fog > 0)

rdb_en = analyze_readability(SAMPLE_EN, "en")
check_true("wynik EN 0-100", 0 <= rdb_en.score <= 100)
check_true("Flesch policzony", rdb_en.flesch != 0)

# --- pusty tekst ----------------------------------------------------------

check("pusty raport sylab", analyze_syllables("", "pl").total_lines, 0)
check("pusty raport rymow", analyze_rhymes("", "pl").scheme, "")
check("pusty raport powtorzen", analyze_repetition("", "pl").total_words, 0)
check("pusty raport czytelnosci", analyze_readability("", "pl").words, 0)

# --- eksport --------------------------------------------------------------

meta = SongMeta(title="Biegne przez deszcz", artist="Test",
                style="indie folk, acoustic guitar", tempo="96", key="Am")

suno = export_suno(SAMPLE_PL, meta)
check_true("Suno zawiera znacznik sekcji", "[Verse 1]" in suno)
check_true("Suno tlumaczy [Zwrotka 1]", "[Zwrotka 1]" not in suno)
check_true("Suno zawiera refren", "[Chorus]" in suno)
check_true("Suno ma pole stylu", "Style of Music" in suno)

udio = export_udio(SAMPLE_EN, meta)
check_true("Udio zawiera Prompt", "Prompt:" in udio)

# autotagowanie tekstu bez znacznikow
plain_blocks = "Wers jeden\nWers dwa\n\nRefren tu\n\nWers trzy\nWers cztery\n\nRefren tu\n"
tagged = export_suno(plain_blocks, SongMeta(), include_meta=False)
check_true("autotag dodal [Chorus]", "[Chorus]" in tagged)
check_true("autotag dodal [Verse 1]", "[Verse 1]" in tagged)

md = export_markdown(SAMPLE_PL, meta, "pl")
check_true("Markdown ma sekcje rymow", "Rymy" in md)
check_true("Markdown ma sekcje czytelnosci", "Czytelnosc" in md)

# --- dokument -------------------------------------------------------------

doc = Document(meta=meta, text=SAMPLE_PL, text_language="pl")
data = doc.to_dict()
restored = Document.from_dict(data)
check("dokument - tekst", restored.text, SAMPLE_PL)
check("dokument - tytul", restored.meta.title, meta.title)
check("dokument - jezyk", restored.text_language, "pl")

# zapis i odczyt z dysku
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    target = str(Path(tmp) / "utwor.lyr")
    saved_path = Document(meta=meta, text=SAMPLE_PL, text_language="pl").save(target)
    reloaded = Document.load(saved_path)
    check("plik .lyr - tekst", reloaded.text, SAMPLE_PL)
    check("plik .lyr - tytul", reloaded.meta.title, meta.title)
    check("plik .lyr - styl", reloaded.meta.style, meta.style)

    txt_path = str(Path(tmp) / "utwor.txt")
    Document(text=SAMPLE_PL).save(txt_path)
    from_txt = Document.load(txt_path)
    check("plik .txt - tekst", from_txt.text, SAMPLE_PL)
    check("plik .txt - tytul z nazwy pliku", from_txt.meta.title, "utwor")


# --- wynik ----------------------------------------------------------------

if FAILURES:
    print(f"NIEPOWODZENIA ({len(FAILURES)}):")
    for failure in FAILURES:
        print("  -", failure)
    raise SystemExit(1)

print("Wszystkie testy analityczne przeszly.")
