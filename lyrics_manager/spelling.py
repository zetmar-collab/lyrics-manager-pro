"""Sprawdzanie pisowni na slownikach Hunspell (.dic + .aff).

To ten sam format, ktorego uzywaja LibreOffice, FreeOffice i Firefox, wiec
slownik pobrany dla LibreOffice zadziala tutaj bez zmian. Silnikiem jest
`spylls` - czysta implementacja Hunspella w Pythonie, bez bibliotek natywnych.
"""

from __future__ import annotations

import json
import re
import shutil
import threading
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .config import data_dir

try:  # pragma: no cover - zaleznosc opcjonalna
    from spylls.hunspell import Dictionary as _HunspellDictionary
    SPYLLS_AVAILABLE = True
except Exception:  # pragma: no cover
    _HunspellDictionary = None
    SPYLLS_AVAILABLE = False


# --- katalog slownikow ----------------------------------------------------

def dictionaries_dir() -> Path:
    path = data_dir() / "dictionaries"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class DictionarySource:
    """Slownik mozliwy do pobrania."""
    code: str            # pl_PL, en_US, en_GB
    lang: str            # pl | en
    label: str
    dic_url: str
    aff_url: str
    page_url: str        # strona do przejrzenia / recznego pobrania
    approx_mb: float
    license: str


_LO_RAW = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master"
_LO_TREE = "https://github.com/LibreOffice/dictionaries/tree/master"

CATALOG: list[DictionarySource] = [
    DictionarySource(
        code="pl_PL", lang="pl", label="Polski (pl_PL)",
        dic_url=f"{_LO_RAW}/pl_PL/pl_PL.dic",
        aff_url=f"{_LO_RAW}/pl_PL/pl_PL.aff",
        page_url=f"{_LO_TREE}/pl_PL",
        approx_mb=5.4, license="LGPL / MPL / CC-BY-SA (sjp.pl)",
    ),
    DictionarySource(
        code="en_US", lang="en", label="English (en_US)",
        dic_url=f"{_LO_RAW}/en/en_US.dic",
        aff_url=f"{_LO_RAW}/en/en_US.aff",
        page_url=f"{_LO_TREE}/en",
        approx_mb=0.2, license="LGPL / BSD (SCOWL)",
    ),
    DictionarySource(
        code="en_GB", lang="en", label="English (en_GB)",
        dic_url=f"{_LO_RAW}/en/en_GB.dic",
        aff_url=f"{_LO_RAW}/en/en_GB.aff",
        page_url=f"{_LO_TREE}/en",
        approx_mb=0.4, license="LGPL / BSD (SCOWL)",
    ),
]

# Strony, na ktorych mozna poszukac slownikow samodzielnie.
MANUAL_LINKS = [
    ("LibreOffice — słowniki (wszystkie języki)",
     "https://github.com/LibreOffice/dictionaries"),
    ("LibreOffice Extensions — English dictionaries",
     "https://extensions.libreoffice.org/en/extensions/show/english-dictionaries"),
    ("sjp.pl — polski słownik ortograficzny (Hunspell)",
     "https://sjp.pl/slownik/ort/"),
]

# Miejsca, w ktorych moga juz lezec slowniki zainstalowane z LibreOffice.
SYSTEM_DICT_PATHS = [
    Path(r"C:\Program Files\LibreOffice\share\extensions"),
    Path(r"C:\Program Files (x86)\LibreOffice\share\extensions"),
    Path(r"C:\Program Files\LibreOffice\share\dict\ooo"),
    Path(r"C:\Program Files (x86)\OpenOffice 4\share\dict\ooo"),
    Path(r"C:\Program Files\SoftMaker\FreeOffice\dictionaries"),
    Path.home() / "AppData/Roaming/LibreOffice/4/user/uno_packages/cache/uno_packages",
]


def source_for(code: str) -> DictionarySource | None:
    return next((s for s in CATALOG if s.code == code), None)


def sources_for_language(lang: str) -> list[DictionarySource]:
    return [s for s in CATALOG if s.lang == lang]


def installed_codes() -> list[str]:
    """Kody slownikow obecnych w katalogu aplikacji."""
    out = []
    for dic in dictionaries_dir().glob("*.dic"):
        if dic.with_suffix(".aff").exists():
            out.append(dic.stem)
    return sorted(out)


def find_system_dictionaries() -> dict[str, Path]:
    """Szuka slownikow zainstalowanych przez LibreOffice / OpenOffice.

    Zwraca {kod: sciezka_do_pliku_dic}.
    """
    found: dict[str, Path] = {}
    for base in SYSTEM_DICT_PATHS:
        if not base.exists():
            continue
        try:
            for dic in base.rglob("*.dic"):
                if dic.stem in found:
                    continue
                if dic.with_suffix(".aff").exists():
                    found[dic.stem] = dic
        except OSError:
            continue
    return found


def import_system_dictionary(dic_path: Path) -> str:
    """Kopiuje pare .dic/.aff do katalogu aplikacji. Zwraca kod slownika."""
    aff_path = dic_path.with_suffix(".aff")
    if not aff_path.exists():
        raise FileNotFoundError(f"Brak pliku {aff_path.name}")
    target = dictionaries_dir()
    shutil.copy2(dic_path, target / dic_path.name)
    shutil.copy2(aff_path, target / aff_path.name)
    return dic_path.stem


def import_archive(archive_path: Path) -> list[str]:
    """Wypakowuje slowniki z pliku .oxt / .zip (tak dystrybuuje je LibreOffice).

    Zwraca liste kodow slownikow, ktore udalo sie zainstalowac.
    """
    target = dictionaries_dir()
    installed: list[str] = []
    with zipfile.ZipFile(archive_path) as zf:
        names = zf.namelist()
        stems = {
            Path(n).stem for n in names
            if n.lower().endswith(".dic")
        }
        for stem in sorted(stems):
            dic_name = next((n for n in names
                             if Path(n).stem == stem and n.lower().endswith(".dic")), None)
            aff_name = next((n for n in names
                             if Path(n).stem == stem and n.lower().endswith(".aff")), None)
            if not dic_name or not aff_name:
                continue
            (target / f"{stem}.dic").write_bytes(zf.read(dic_name))
            (target / f"{stem}.aff").write_bytes(zf.read(aff_name))
            installed.append(stem)
    return installed


def import_single_pair(dic_path: Path) -> str:
    """Instaluje wskazany przez uzytkownika plik .dic wraz z sasiadujacym .aff."""
    return import_system_dictionary(dic_path)


def remove_dictionary(code: str) -> None:
    base = dictionaries_dir()
    for suffix in (".dic", ".aff"):
        path = base / f"{code}{suffix}"
        if path.exists():
            path.unlink()


# --- pobieranie -----------------------------------------------------------

def download_dictionary(
    source: DictionarySource,
    progress: Callable[[int, int], None] | None = None,
    cancel: threading.Event | None = None,
) -> str:
    """Pobiera pare .dic/.aff. Zwraca kod slownika. Rzuca przy bledzie.

    Najpierw zapisuje do plikow tymczasowych, zeby przerwane pobieranie nie
    zostawilo uszkodzonego slownika.
    """
    import requests  # lokalnie: modul dziala takze bez sieci

    target = dictionaries_dir()
    temp_files: list[Path] = []

    try:
        parts = [(source.aff_url, f"{source.code}.aff"),
                 (source.dic_url, f"{source.code}.dic")]
        total_expected = int(source.approx_mb * 1024 * 1024) or 1
        downloaded = 0

        for url, filename in parts:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            tmp = target / f"{filename}.part"
            temp_files.append(tmp)
            with tmp.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if cancel is not None and cancel.is_set():
                        raise InterruptedError("cancelled")
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total_expected)
            response.close()

        for tmp in temp_files:
            final = tmp.with_suffix("")
            if final.exists():
                final.unlink()
            tmp.rename(final)
        temp_files.clear()
        return source.code
    finally:
        for tmp in temp_files:
            try:
                tmp.unlink()
            except OSError:
                pass


# --- slownik uzytkownika --------------------------------------------------

class PersonalDictionary:
    """Wlasne slowa autora - nazwy wlasne, neologizmy, celowe zapisy gwarowe."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (data_dir() / "personal_dictionary.json")
        self._words: dict[str, set[str]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self._words = {
            lang: {w.lower() for w in words}
            for lang, words in raw.items() if isinstance(words, list)
        }

    def save(self) -> None:
        try:
            self.path.write_text(
                json.dumps({k: sorted(v) for k, v in self._words.items()},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def words(self, lang: str) -> list[str]:
        return sorted(self._words.get(lang, set()))

    def contains(self, word: str, lang: str) -> bool:
        return word.lower() in self._words.get(lang, set())

    def add(self, word: str, lang: str) -> None:
        clean = word.strip().lower()
        if not clean:
            return
        self._words.setdefault(lang, set()).add(clean)
        self.save()

    def remove(self, word: str, lang: str) -> None:
        self._words.get(lang, set()).discard(word.strip().lower())
        self.save()

    def clear(self, lang: str) -> None:
        self._words.pop(lang, None)
        self.save()


# --- sprawdzanie pisowni --------------------------------------------------

# Slowo z apostrofem i lacznikiem; cyfry i znaczniki sekcji pomijamy osobno.
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
SECTION_RE = re.compile(r"^\s*[\[\({].*[\]\)}]\s*$")


@dataclass
class Misspelling:
    line: int          # numer wersu, 1-based
    column: int        # pozycja w wersie, 0-based
    word: str

    @property
    def end_column(self) -> int:
        return self.column + len(self.word)


@dataclass
class SpellReport:
    problems: list[Misspelling] = field(default_factory=list)
    unique: list[tuple[str, int]] = field(default_factory=list)  # (slowo, ile razy)
    checked_words: int = 0

    @property
    def error_count(self) -> int:
        return len(self.problems)

    @property
    def accuracy(self) -> float:
        if not self.checked_words:
            return 100.0
        return 100.0 * (1 - self.error_count / self.checked_words)


class SpellChecker:
    """Sprawdza pisownie w jednym jezyku. Ladowanie slownika jest leniwe."""

    def __init__(self, personal: PersonalDictionary | None = None) -> None:
        self.personal = personal or PersonalDictionary()
        self._dictionaries: dict[str, object] = {}
        self._cache: dict[tuple[str, str], bool] = {}
        self._ignored: dict[str, set[str]] = {}
        self._lock = threading.Lock()

    # -- stan -------------------------------------------------------------

    @staticmethod
    def engine_available() -> bool:
        return SPYLLS_AVAILABLE

    @staticmethod
    def dictionary_installed(code: str) -> bool:
        base = dictionaries_dir()
        return (base / f"{code}.dic").exists() and (base / f"{code}.aff").exists()

    def is_loaded(self, code: str) -> bool:
        return code in self._dictionaries

    def loaded_codes(self) -> list[str]:
        return sorted(self._dictionaries)

    # -- ladowanie --------------------------------------------------------

    def load(self, code: str) -> None:
        """Wczytuje slownik. Wolne dla duzych jezykow - wolaj w osobnym watku."""
        if not SPYLLS_AVAILABLE:
            raise RuntimeError("NO_ENGINE")
        if code in self._dictionaries:
            return
        if not self.dictionary_installed(code):
            raise FileNotFoundError(code)
        base = dictionaries_dir() / code
        dictionary = _HunspellDictionary.from_files(str(base))
        with self._lock:
            self._dictionaries[code] = dictionary
            self._cache = {k: v for k, v in self._cache.items() if k[0] != code}

    def unload(self, code: str) -> None:
        with self._lock:
            self._dictionaries.pop(code, None)
            self._cache = {k: v for k, v in self._cache.items() if k[0] != code}

    # -- sprawdzanie ------------------------------------------------------

    def ignore(self, word: str, code: str) -> None:
        self._ignored.setdefault(code, set()).add(word.lower())

    def ignored(self, code: str) -> set[str]:
        return self._ignored.get(code, set())

    def add_to_personal(self, word: str, lang: str, code: str) -> None:
        self.personal.add(word, lang)
        self._cache.pop((code, word.lower()), None)

    def check_word(self, word: str, code: str, lang: str) -> bool:
        """True = slowo poprawne (albo nie da sie sprawdzic)."""
        dictionary = self._dictionaries.get(code)
        if dictionary is None:
            return True
        clean = word.strip("'’-")
        if not clean or clean.isdigit():
            return True
        lowered = clean.lower()
        if lowered in self._ignored.get(code, set()):
            return True
        if self.personal.contains(lowered, lang):
            return True

        key = (code, clean)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            ok = bool(dictionary.lookup(clean))
            if not ok and clean != lowered:
                # WERSY PISANE WERSALIKAMI i Slowa Na Poczatku Wersu
                ok = bool(dictionary.lookup(lowered)) or bool(
                    dictionary.lookup(lowered.capitalize())
                )
        except Exception:  # noqa: BLE001 - blad slownika nie moze blokowac pisania
            ok = True

        self._cache[key] = ok
        return ok

    def suggest(self, word: str, code: str, limit: int = 7) -> list[str]:
        dictionary = self._dictionaries.get(code)
        if dictionary is None:
            return []
        try:
            out: list[str] = []
            for candidate in dictionary.suggest(word.strip("'’-")):
                out.append(candidate)
                if len(out) >= limit:
                    break
            return out
        except Exception:  # noqa: BLE001
            return []

    def check_text(self, text: str, code: str, lang: str) -> SpellReport:
        report = SpellReport()
        if code not in self._dictionaries:
            return report

        counts: dict[str, int] = {}
        for line_no, line in enumerate(text.splitlines(), start=1):
            if SECTION_RE.match(line):
                continue
            for match in WORD_RE.finditer(line):
                word = match.group(0)
                report.checked_words += 1
                if self.check_word(word, code, lang):
                    continue
                report.problems.append(Misspelling(line_no, match.start(), word))
                counts[word] = counts.get(word, 0) + 1

        report.unique = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
        return report


def default_code_for(lang: str, installed: Iterable[str] | None = None) -> str | None:
    """Wybiera slownik dla jezyka sposrod zainstalowanych."""
    codes = list(installed) if installed is not None else installed_codes()
    preferred = [s.code for s in sources_for_language(lang)]
    for code in preferred:
        if code in codes:
            return code
    # slownik spoza katalogu, np. wgrany recznie (pl_PL, en_AU, de_DE...)
    for code in codes:
        if code.lower().startswith(lang.lower()):
            return code
    return None
