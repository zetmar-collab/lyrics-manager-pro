# Historia zmian / Changelog

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
wersjonowanie zgodne z [SemVer](https://semver.org/lang/pl/).

## [1.0.0] — 2026-08-01

Pierwsze wydanie.

### Dodane

- **Licznik sylab** — na żywo w rynnie edytora, osobne algorytmy dla polskiego
  (grupy samogłoskowe z regułą zmiękczającego „i") i angielskiego (heurystyka
  z listą wyjątków). Statystyki, równomierność wersów, rozkład długości,
  podsumowanie per sekcja.
- **Analiza rymów** — klasyfikacja na dokładne, niedokładne, asonanse
  i powtórzenia słowa, oparta na uproszczonej transkrypcji fonetycznej PL/EN.
  Schemat rymów, gęstość, rymy wewnętrzne, kolorowanie w tekście, wyszukiwarka
  rymów.
- **Wyszukiwanie powtórzeń** — słowa, frazy (n-gramy 2–5) i całe wersy,
  z podświetlaniem w edytorze i skokiem do wersu.
- **Ocena czytelności** — FOG i indeks Pisarka dla polskiego, Flesch
  i Flesch-Kincaid dla angielskiego, plus autorski wskaźnik śpiewalności.
- **Sprawdzanie pisowni** — słowniki Hunspell (`.dic` + `.aff`), te same co
  w LibreOffice. Podkreślanie błędów, podpowiedzi w menu podręcznym, zamiana
  wszystkich wystąpień, własny słownik autora. Pobieranie słowników z poziomu
  programu, import z pliku `.oxt` i wykrywanie słowników LibreOffice.
- **Asystent AI** — dwa silniki: Ollama (lokalnie) i OpenRouter (chmura),
  11 zadań, odpowiedź strumieniowa z możliwością przerwania. Prompt zawiera
  kontekst utworu: schemat rymów i liczbę sylab w wersach.
- **Eksport do Suno i Udio** — normalizacja znaczników sekcji, automatyczne
  rozpoznanie zwrotek i refrenu, pole „Style of Music", kontrola limitu znaków.
  Dodatkowo eksport do czystego tekstu i Markdown z pełnym raportem.
- **Historia zmian** — migawki w bazie SQLite, kolorowany diff, przywracanie
  wersji, autozapis.
- **Interfejs dwujęzyczny** — trzy niezależne przełączniki: język interfejsu,
  język tekstu i język odpowiedzi AI. Motyw jasny i ciemny.
- **Skróty klawiszowe** — 38 pozycji w siedmiu grupach.
- **Instrukcja obsługi w programie** (F1) — 12 sekcji po polsku i angielsku,
  z możliwością zapisania do pliku Markdown.
- **Instalator** dla Windows, instalacja per użytkownik bez praw
  administratora, skojarzenie plików `.lyr`, skróty w Menu Start i na pulpicie.

### Uwagi techniczne

- Aplikacja jest jednym plikiem `.exe` (~18 MB) i nie wymaga instalacji Pythona.
- Słowniki pisowni nie są dołączone do instalatora ze względu na ich własne
  licencje — program pobiera je na żądanie z repozytorium LibreOffice.
- Dane użytkownika (ustawienia, historia, słowniki) są przechowywane
  w `%APPDATA%\LyricsManagerPro` i nie są usuwane przy aktualizacji.

---

## [1.0.0] — 2026-08-01 (English)

First release.

### Added

- **Syllable counter** with separate Polish and English algorithms, live in the
  editor gutter; evenness, distribution and per-section statistics.
- **Rhyme analysis** — perfect, slant, assonance and same-word classification
  from a simplified PL/EN phonetic transcription. Rhyme scheme, density,
  internal rhymes, in-text colouring, rhyme finder.
- **Repetition finder** — words, phrases (2–5-word n-grams) and whole lines,
  highlighted in the editor with jump-to-line.
- **Readability** — FOG and Pisarek for Polish, Flesch and Flesch-Kincaid for
  English, plus an original singability measure.
- **Spell checking** on Hunspell dictionaries, the same ones LibreOffice uses,
  with in-app download, `.oxt` import and LibreOffice dictionary detection.
- **AI assistant** with two engines (local Ollama, cloud OpenRouter), 11 tasks
  and streaming output that can be interrupted.
- **Suno and Udio export** with section tag normalisation and character limits,
  plus plain text and Markdown-with-analysis export.
- **Change history** — SQLite snapshots, colour diff, restore, autosave.
- **Bilingual interface** with three independent language switches, light and
  dark theme.
- **38 keyboard shortcuts** and a built-in **user guide** (F1) in both
  languages, exportable to Markdown.
- **Windows installer** — per-user install with no administrator rights,
  `.lyr` file association, Start Menu and desktop shortcuts.
