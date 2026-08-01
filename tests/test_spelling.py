"""Testy sprawdzania pisowni.

Czesc testow wymaga zainstalowanych slownikow Hunspell - jesli ich nie ma,
te testy sa pomijane z wyraznym komunikatem, a reszta i tak sie wykona.
Uruchomienie: python tests\\test_spelling.py
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyrics_manager.spelling import (
    CATALOG, MANUAL_LINKS, PersonalDictionary, SpellChecker, default_code_for,
    dictionaries_dir, import_archive, installed_codes, source_for,
)

FAILURES: list[str] = []
SKIPPED: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f"{label}: oczekiwano {expected!r}, jest {actual!r}")


def check_true(label: str, condition: bool) -> None:
    if not condition:
        FAILURES.append(f"{label}: warunek nie zostal spelniony")


# --- katalog slownikow ----------------------------------------------------

check_true("katalog ma polski", any(s.code == "pl_PL" for s in CATALOG))
check_true("katalog ma angielski", any(s.code == "en_US" for s in CATALOG))
check_true("wszystkie zrodla maja adresy", all(
    s.dic_url.startswith("https://") and s.aff_url.startswith("https://")
    and s.page_url.startswith("https://") for s in CATALOG
))
check_true("linki reczne sa adresami https",
           all(url.startswith("https://") for _label, url in MANUAL_LINKS))
check("source_for zwraca wlasciwe zrodlo", source_for("pl_PL").lang, "pl")
check("source_for nieznanego kodu", source_for("xx_XX"), None)

check("wybor slownika dla pl", default_code_for("pl", ["en_US", "pl_PL"]), "pl_PL")
check("wybor slownika dla en", default_code_for("en", ["en_US", "pl_PL"]), "en_US")
check("preferencja en_US przed en_GB",
      default_code_for("en", ["en_GB", "en_US"]), "en_US")
check("brak slownika dla jezyka", default_code_for("pl", ["en_US"]), None)
check("slownik spoza katalogu", default_code_for("de", ["de_DE"]), "de_DE")

# --- slownik uzytkownika --------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    personal = PersonalDictionary(Path(tmp) / "personal.json")
    personal.add("Wisławą", "pl")
    personal.add("SZYMBORSKA", "pl")
    personal.add("gonna", "en")

    check_true("slowo dodane", personal.contains("wisławą", "pl"))
    check_true("wielkosc liter bez znaczenia", personal.contains("Szymborska", "pl"))
    check_true("jezyki sa rozdzielone", not personal.contains("gonna", "pl"))
    check("liczba slow pl", len(personal.words("pl")), 2)

    reloaded = PersonalDictionary(Path(tmp) / "personal.json")
    check_true("slownik przetrwal zapis", reloaded.contains("wisławą", "pl"))

    reloaded.remove("wisławą", "pl")
    check_true("slowo usuniete", not reloaded.contains("wisławą", "pl"))

# --- import archiwum .oxt -------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    archive = Path(tmp) / "test_dict.oxt"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("dictionaries/xx_XX.dic", "2\nkot\npies\n")
        zf.writestr("dictionaries/xx_XX.aff", "SET UTF-8\n")
        zf.writestr("description.xml", "<x/>")
    installed = import_archive(archive)
    check("import .oxt zwraca kod", installed, ["xx_XX"])
    check_true("plik .dic na miejscu", (dictionaries_dir() / "xx_XX.dic").exists())
    check_true("plik .aff na miejscu", (dictionaries_dir() / "xx_XX.aff").exists())
    # sprzatanie po tescie
    for suffix in (".dic", ".aff"):
        (dictionaries_dir() / f"xx_XX{suffix}").unlink(missing_ok=True)

# --- silnik ---------------------------------------------------------------

if not SpellChecker.engine_available():
    SKIPPED.append("silnik spylls nie jest zainstalowany")
else:
    codes = installed_codes()

    SAMPLE_PL = """[Zwrotka 1]
Wracam do domu nocną drogą
Światła miasta gasną z tyłu
Nie ma juz nic co mnie tu trzyma
Tylko cien na mokrym pyłu
"""
    SAMPLE_EN = """[Verse 1]
I walk the road back home tonite
The city lights are fading slow
Just shadowz on the road below
"""

    if "pl_PL" in codes:
        sc = SpellChecker(PersonalDictionary(Path(tempfile.gettempdir()) / "lm_test_pl.json"))
        sc.load("pl_PL")

        check_true("poprawne slowo PL", sc.check_word("droga", "pl_PL", "pl"))
        check_true("poprawne slowo PL z diakrytykami",
                   sc.check_word("nocną", "pl_PL", "pl"))
        check_true("blad PL wykryty", not sc.check_word("zmenczony", "pl_PL", "pl"))
        check_true("brak diakrytyku to blad", not sc.check_word("juz", "pl_PL", "pl"))

        report = sc.check_text(SAMPLE_PL, "pl_PL", "pl")
        words = {p.word for p in report.problems}
        check_true("wykryto 'juz'", "juz" in words)
        check_true("wykryto 'cien'", "cien" in words)
        check_true("znacznik sekcji pominiety",
                   not any(p.line == 1 for p in report.problems))
        check_true("poprawne slowa nie sa zglaszane", "Wracam" not in words)
        check_true("liczba sprawdzonych slow", report.checked_words > 15)
        check_true("poprawnosc miedzy 0 a 100", 0 <= report.accuracy <= 100)

        positions = {(p.line, p.column, p.word) for p in report.problems}
        check_true("pozycja bledu poprawna", (4, 7, "juz") in positions)

        suggestions = sc.suggest("zmenczony", "pl_PL")
        check_true("podpowiedzi PL niepuste", len(suggestions) > 0)
        check_true("podpowiedz zawiera poprawne slowo",
                   any("zmęczony" == s for s in suggestions))

        # slownik uzytkownika wycisza blad
        sc.add_to_personal("zmenczony", "pl", "pl_PL")
        check_true("slowo z wlasnego slownika jest poprawne",
                   sc.check_word("zmenczony", "pl_PL", "pl"))
        sc.personal.remove("zmenczony", "pl")

        # ignorowanie w sesji
        sc.ignore("cien", "pl_PL")
        check_true("zignorowane slowo jest poprawne",
                   sc.check_word("cien", "pl_PL", "pl"))
    else:
        SKIPPED.append("brak slownika pl_PL - pomijam testy polskie")

    if "en_US" in codes:
        sc_en = SpellChecker(
            PersonalDictionary(Path(tempfile.gettempdir()) / "lm_test_en.json"))
        sc_en.load("en_US")

        check_true("poprawne slowo EN", sc_en.check_word("shadow", "en_US", "en"))
        check_true("blad EN wykryty", not sc_en.check_word("shadowz", "en_US", "en"))

        report_en = sc_en.check_text(SAMPLE_EN, "en_US", "en")
        words_en = {p.word for p in report_en.problems}
        check_true("wykryto 'tonite'", "tonite" in words_en)
        check_true("wykryto 'shadowz'", "shadowz" in words_en)
        check_true("'lights' jest poprawne", "lights" not in words_en)

        suggestions_en = sc_en.suggest("shadowz", "en_US")
        check_true("podpowiedzi EN zawieraja 'shadows'", "shadows" in suggestions_en)
    else:
        SKIPPED.append("brak slownika en_US - pomijam testy angielskie")

    # bez zaladowanego slownika sprawdzanie nie zglasza nic
    empty = SpellChecker(PersonalDictionary(Path(tempfile.gettempdir()) / "lm_test_x.json"))
    check_true("bez slownika brak bledow",
               empty.check_text(SAMPLE_PL, "zz_ZZ", "pl").error_count == 0)
    check_true("bez slownika slowo uznane za poprawne",
               empty.check_word("qwertyuiop", "zz_ZZ", "pl"))

# --- wynik ----------------------------------------------------------------

for note in SKIPPED:
    print("POMINIETO:", note)

if FAILURES:
    print(f"NIEPOWODZENIA ({len(FAILURES)}):")
    for failure in FAILURES:
        print("  -", failure)
    raise SystemExit(1)

print("Wszystkie testy pisowni przeszly.")
