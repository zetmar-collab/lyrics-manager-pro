"""Warstwa tlumaczen interfejsu (PL / EN).

Uzycie:
    from .i18n import tr, set_ui_language
    tr("menu.file")
"""

from __future__ import annotations

from typing import Callable

LANGUAGES = ("pl", "en")
LANGUAGE_LABELS = {"pl": "Polski", "en": "English"}

_current = "pl"
_listeners: list[Callable[[str], None]] = []

STRINGS: dict[str, dict[str, str]] = {
    # --- ogolne / okno ---------------------------------------------------
    "app.title": {"pl": "Lyrics Manager Pro", "en": "Lyrics Manager Pro"},
    "app.subtitle": {
        "pl": "Warsztat autora tekstów piosenek",
        "en": "The songwriter's workbench",
    },
    "app.untitled": {"pl": "Bez tytułu", "en": "Untitled"},
    "app.modified": {"pl": "niezapisane zmiany", "en": "unsaved changes"},
    "app.saved": {"pl": "zapisano", "en": "saved"},
    "app.ready": {"pl": "Gotowe", "en": "Ready"},
    # --- pasek narzedzi --------------------------------------------------
    "tb.new": {"pl": "Nowy", "en": "New"},
    "tb.open": {"pl": "Otwórz", "en": "Open"},
    "tb.save": {"pl": "Zapisz", "en": "Save"},
    "tb.save_as": {"pl": "Zapisz jako", "en": "Save as"},
    "tb.export": {"pl": "Eksport", "en": "Export"},
    "tb.analyze": {"pl": "Analizuj", "en": "Analyze"},
    "tb.settings": {"pl": "Ustawienia", "en": "Settings"},
    "tb.ui_lang": {"pl": "Język UI", "en": "UI language"},
    "tb.text_lang": {"pl": "Język tekstu", "en": "Lyrics language"},
    "tb.theme": {"pl": "Motyw", "en": "Theme"},
    "theme.light": {"pl": "Jasny", "en": "Light"},
    "theme.dark": {"pl": "Ciemny", "en": "Dark"},
    "theme.system": {"pl": "Systemowy", "en": "System"},
    # --- metryczka utworu ------------------------------------------------
    "meta.title": {"pl": "Tytuł", "en": "Title"},
    "meta.artist": {"pl": "Wykonawca", "en": "Artist"},
    "meta.style": {"pl": "Styl / gatunek", "en": "Style / genre"},
    "meta.tempo": {"pl": "Tempo (BPM)", "en": "Tempo (BPM)"},
    "meta.key": {"pl": "Tonacja", "en": "Key"},
    "meta.notes": {"pl": "Notatki", "en": "Notes"},
    # --- zakladki paneli -------------------------------------------------
    "tab.syllables": {"pl": "Sylaby", "en": "Syllables"},
    "tab.rhymes": {"pl": "Rymy", "en": "Rhymes"},
    "tab.repetitions": {"pl": "Powtórzenia", "en": "Repetitions"},
    "tab.readability": {"pl": "Czytelność", "en": "Readability"},
    "tab.ai": {"pl": "AI", "en": "AI"},
    "tab.history": {"pl": "Historia", "en": "History"},
    "tab.export": {"pl": "Eksport", "en": "Export"},
    # --- sylaby ----------------------------------------------------------
    "syl.header": {"pl": "Licznik sylab", "en": "Syllable counter"},
    "syl.total_lines": {"pl": "Wersy", "en": "Lines"},
    "syl.total_syllables": {"pl": "Sylaby razem", "en": "Total syllables"},
    "syl.avg": {"pl": "Średnio na wers", "en": "Average per line"},
    "syl.min_max": {"pl": "Min / Maks", "en": "Min / Max"},
    "syl.variance": {"pl": "Równomierność", "en": "Evenness"},
    "syl.words": {"pl": "Słowa", "en": "Words"},
    "syl.chars": {"pl": "Znaki", "en": "Characters"},
    "syl.per_line": {"pl": "Rozkład długości wersów", "en": "Line length distribution"},
    "syl.hint": {
        "pl": "Liczby po lewej stronie edytora to liczba sylab w wersie.",
        "en": "Numbers on the left of the editor are syllables per line.",
    },
    "syl.sections": {"pl": "Sekcje utworu", "en": "Song sections"},
    "syl.unit": {"pl": "sylab", "en": "syllables"},
    # --- rymy ------------------------------------------------------------
    "rhy.header": {"pl": "Analiza rymów", "en": "Rhyme analysis"},
    "rhy.scheme": {"pl": "Schemat rymów", "en": "Rhyme scheme"},
    "rhy.groups": {"pl": "Grupy rymów", "en": "Rhyme groups"},
    "rhy.density": {"pl": "Gęstość rymów", "en": "Rhyme density"},
    "rhy.perfect": {"pl": "Rymy dokładne", "en": "Perfect rhymes"},
    "rhy.slant": {"pl": "Rymy niedokładne", "en": "Slant rhymes"},
    "rhy.none": {"pl": "Wersy bez rymu", "en": "Unrhymed lines"},
    "rhy.internal": {"pl": "Rymy wewnętrzne", "en": "Internal rhymes"},
    "rhy.highlight": {"pl": "Podświetl rymy w tekście", "en": "Highlight rhymes in text"},
    "rhy.find_for": {"pl": "Znajdź rymy do słowa", "en": "Find rhymes for word"},
    "rhy.find_btn": {"pl": "Szukaj", "en": "Search"},
    "rhy.suggestions": {"pl": "Propozycje", "en": "Suggestions"},
    "rhy.ai_suggest": {"pl": "Poszukaj rymów przez AI", "en": "Find rhymes with AI"},
    "rhy.type_perfect": {"pl": "dokładny", "en": "perfect"},
    "rhy.type_slant": {"pl": "niedokładny", "en": "slant"},
    "rhy.type_assonance": {"pl": "asonans", "en": "assonance"},
    "rhy.type_identity": {"pl": "powtórzenie słowa", "en": "same word"},
    # --- powtorzenia -----------------------------------------------------
    "rep.header": {"pl": "Wyszukiwanie powtórzeń", "en": "Repetition finder"},
    "rep.words": {"pl": "Powtarzane słowa", "en": "Repeated words"},
    "rep.phrases": {"pl": "Powtarzane frazy", "en": "Repeated phrases"},
    "rep.lines": {"pl": "Powtarzane wersy", "en": "Repeated lines"},
    "rep.count": {"pl": "razy", "en": "times"},
    "rep.lines_col": {"pl": "wersy", "en": "lines"},
    "rep.min_count": {"pl": "Minimalna liczba wystąpień", "en": "Minimum occurrences"},
    "rep.ignore_stopwords": {
        "pl": "Pomijaj słowa funkcyjne (i, w, na…)",
        "en": "Ignore function words (the, a, in…)",
    },
    "rep.diversity": {"pl": "Bogactwo słownictwa", "en": "Lexical diversity"},
    "rep.unique": {"pl": "Słowa unikalne", "en": "Unique words"},
    "rep.none": {"pl": "Nie znaleziono powtórzeń.", "en": "No repetitions found."},
    "rep.hint": {
        "pl": "Powtórzenia w refrenie są pożądane — w zwrotkach zwykle nie.",
        "en": "Repetition in a chorus is good — in verses usually not.",
    },
    # --- czytelnosc ------------------------------------------------------
    "read.header": {"pl": "Ocena czytelności", "en": "Readability score"},
    "read.score": {"pl": "Wynik ogólny", "en": "Overall score"},
    "read.grade": {"pl": "Poziom trudności", "en": "Difficulty level"},
    "read.flesch": {"pl": "Flesch Reading Ease", "en": "Flesch Reading Ease"},
    "read.fog": {"pl": "Indeks FOG", "en": "FOG index"},
    "read.pisarek": {"pl": "Indeks Pisarka", "en": "Pisarek index"},
    "read.fk": {"pl": "Flesch-Kincaid", "en": "Flesch-Kincaid"},
    "read.long_words": {"pl": "Słowa długie (4+ sylaby)", "en": "Long words (4+ syllables)"},
    "read.avg_word": {"pl": "Średnia długość słowa", "en": "Average word length"},
    "read.avg_sentence": {"pl": "Średnia długość zdania", "en": "Average sentence length"},
    "read.singability": {"pl": "Śpiewalność", "en": "Singability"},
    "read.hard_lines": {"pl": "Wersy trudne do zaśpiewania", "en": "Hard-to-sing lines"},
    "read.level.very_easy": {"pl": "Bardzo łatwy", "en": "Very easy"},
    "read.level.easy": {"pl": "Łatwy", "en": "Easy"},
    "read.level.medium": {"pl": "Średni", "en": "Medium"},
    "read.level.hard": {"pl": "Trudny", "en": "Hard"},
    "read.level.very_hard": {"pl": "Bardzo trudny", "en": "Very hard"},
    "read.hint": {
        "pl": "Dla tekstów piosenek celuj w wynik 60–90 — łatwo się je śpiewa i zapamiętuje.",
        "en": "For song lyrics aim for 60–90 — easy to sing and remember.",
    },
    # --- AI --------------------------------------------------------------
    "ai.header": {"pl": "Asystent AI", "en": "AI assistant"},
    "ai.engine": {"pl": "Silnik", "en": "Engine"},
    "ai.engine.openrouter": {"pl": "OpenRouter (chmura)", "en": "OpenRouter (cloud)"},
    "ai.engine.ollama": {"pl": "Ollama (lokalnie)", "en": "Ollama (local)"},
    "ai.model": {"pl": "Model", "en": "Model"},
    "ai.refresh_models": {"pl": "Odśwież modele", "en": "Refresh models"},
    "ai.out_lang": {"pl": "Język odpowiedzi", "en": "Output language"},
    "ai.task": {"pl": "Zadanie", "en": "Task"},
    "ai.scope": {"pl": "Zakres", "en": "Scope"},
    "ai.scope.selection": {"pl": "Zaznaczenie", "en": "Selection"},
    "ai.scope.whole": {"pl": "Cały tekst", "en": "Whole text"},
    "ai.instruction": {"pl": "Dodatkowe wskazówki", "en": "Extra instructions"},
    "ai.instruction_ph": {
        "pl": "np. zachowaj 8 sylab w wersie, ton nostalgiczny…",
        "en": "e.g. keep 8 syllables per line, nostalgic tone…",
    },
    "ai.run": {"pl": "Generuj", "en": "Generate"},
    "ai.stop": {"pl": "Zatrzymaj", "en": "Stop"},
    "ai.insert": {"pl": "Wstaw do tekstu", "en": "Insert into text"},
    "ai.replace": {"pl": "Zastąp zakres", "en": "Replace scope"},
    "ai.copy": {"pl": "Kopiuj", "en": "Copy"},
    "ai.clear": {"pl": "Wyczyść", "en": "Clear"},
    "ai.working": {"pl": "AI pracuje…", "en": "AI is working…"},
    "ai.done": {"pl": "Gotowe", "en": "Done"},
    "ai.stopped": {"pl": "Przerwano", "en": "Stopped"},
    "ai.no_key": {
        "pl": "Brak klucza API OpenRouter. Uzupełnij go w Ustawieniach.",
        "en": "OpenRouter API key missing. Set it in Settings.",
    },
    "ai.no_ollama": {
        "pl": "Nie można połączyć się z Ollamą. Sprawdź, czy działa (ollama serve).",
        "en": "Cannot reach Ollama. Check that it is running (ollama serve).",
    },
    "ai.no_models": {"pl": "Brak modeli", "en": "No models"},
    "ai.empty_input": {"pl": "Brak tekstu do przetworzenia.", "en": "Nothing to process."},
    "ai.temperature": {"pl": "Kreatywność", "en": "Creativity"},
    # --- zadania AI ------------------------------------------------------
    "task.alternatives": {"pl": "Alternatywne wersje", "en": "Alternative versions"},
    "task.rhymes": {"pl": "Propozycje rymów", "en": "Rhyme suggestions"},
    "task.continue": {"pl": "Dopisz dalszy ciąg", "en": "Continue the lyrics"},
    "task.polish": {"pl": "Dopracuj język", "en": "Polish the language"},
    "task.metaphors": {"pl": "Wzbogać obrazowanie", "en": "Enrich imagery"},
    "task.simplify": {"pl": "Uprość i skróć", "en": "Simplify and shorten"},
    "task.fit_syllables": {"pl": "Dopasuj liczbę sylab", "en": "Fit syllable count"},
    "task.translate": {"pl": "Przetłumacz śpiewalnie", "en": "Singable translation"},
    "task.title": {"pl": "Zaproponuj tytuły", "en": "Suggest titles"},
    "task.critique": {"pl": "Recenzja tekstu", "en": "Critique the lyrics"},
    "task.suno_prompt": {"pl": "Zbuduj prompt stylu", "en": "Build a style prompt"},
    # --- historia --------------------------------------------------------
    "hist.header": {"pl": "Historia zmian", "en": "Change history"},
    "hist.snapshot": {"pl": "Zapisz punkt w historii", "en": "Save a snapshot"},
    "hist.label": {"pl": "Opis punktu", "en": "Snapshot label"},
    "hist.restore": {"pl": "Przywróć", "en": "Restore"},
    "hist.preview": {"pl": "Podgląd", "en": "Preview"},
    "hist.diff": {"pl": "Różnice", "en": "Differences"},
    "hist.delete": {"pl": "Usuń", "en": "Delete"},
    "hist.auto": {"pl": "auto", "en": "auto"},
    "hist.manual": {"pl": "ręczny", "en": "manual"},
    "hist.empty": {"pl": "Historia jest pusta.", "en": "History is empty."},
    "hist.restored": {"pl": "Przywrócono wersję z historii.", "en": "Version restored."},
    "hist.confirm_restore": {
        "pl": "Przywrócić tę wersję? Obecny tekst zostanie zapisany w historii.",
        "en": "Restore this version? Current text will be snapshotted first.",
    },
    "hist.confirm_delete": {"pl": "Usunąć ten punkt historii?", "en": "Delete this snapshot?"},
    "hist.autosave_every": {"pl": "Autozapis co (min)", "en": "Autosave every (min)"},
    "hist.words_changed": {"pl": "zmienionych wersów", "en": "changed lines"},
    "hist.identical": {"pl": "Brak różnic wobec bieżącego tekstu.",
                       "en": "No differences from the current text."},
    # --- eksport ---------------------------------------------------------
    "exp.header": {"pl": "Eksport", "en": "Export"},
    "exp.target": {"pl": "Format", "en": "Format"},
    "exp.suno": {"pl": "Suno", "en": "Suno"},
    "exp.udio": {"pl": "Udio", "en": "Udio"},
    "exp.plain": {"pl": "Czysty tekst", "en": "Plain text"},
    "exp.markdown": {"pl": "Markdown (z analizą)", "en": "Markdown (with analysis)"},
    "exp.style_prompt": {"pl": "Opis stylu (style prompt)", "en": "Style prompt"},
    "exp.preview": {"pl": "Podgląd eksportu", "en": "Export preview"},
    "exp.copy": {"pl": "Kopiuj do schowka", "en": "Copy to clipboard"},
    "exp.save_file": {"pl": "Zapisz do pliku", "en": "Save to file"},
    "exp.copied": {"pl": "Skopiowano do schowka.", "en": "Copied to clipboard."},
    "exp.saved": {"pl": "Zapisano plik.", "en": "File saved."},
    "exp.chars": {"pl": "znaków", "en": "characters"},
    "exp.limit_warn": {
        "pl": "Uwaga: tekst przekracza limit {limit} znaków dla {target}.",
        "en": "Warning: text exceeds the {limit} character limit for {target}.",
    },
    "exp.autotag": {"pl": "Automatycznie dodaj znaczniki sekcji", "en": "Auto-add section tags"},
    "exp.include_meta": {"pl": "Dołącz metryczkę", "en": "Include metadata"},
    # --- ustawienia ------------------------------------------------------
    "set.header": {"pl": "Ustawienia", "en": "Settings"},
    "set.general": {"pl": "Ogólne", "en": "General"},
    "set.ai": {"pl": "Silniki AI", "en": "AI engines"},
    "set.editor": {"pl": "Edytor", "en": "Editor"},
    "set.or_key": {"pl": "Klucz API OpenRouter", "en": "OpenRouter API key"},
    "set.or_key_hint": {
        "pl": "Klucz zdobędziesz na openrouter.ai/keys. Zapisywany lokalnie na tym komputerze.",
        "en": "Get a key at openrouter.ai/keys. Stored locally on this computer.",
    },
    "set.or_model": {"pl": "Domyślny model OpenRouter", "en": "Default OpenRouter model"},
    "set.ollama_url": {"pl": "Adres serwera Ollama", "en": "Ollama server URL"},
    "set.ollama_model": {"pl": "Domyślny model Ollama", "en": "Default Ollama model"},
    "set.test": {"pl": "Testuj połączenie", "en": "Test connection"},
    "set.test_ok": {"pl": "Połączenie działa.", "en": "Connection works."},
    "set.test_fail": {"pl": "Błąd połączenia: {err}", "en": "Connection error: {err}"},
    "set.font_size": {"pl": "Rozmiar czcionki edytora", "en": "Editor font size"},
    "set.font_family": {"pl": "Czcionka edytora", "en": "Editor font"},
    "set.show_syllables": {"pl": "Pokazuj licznik sylab", "en": "Show syllable gutter"},
    "set.live_analysis": {"pl": "Analiza na żywo", "en": "Live analysis"},
    "set.save": {"pl": "Zapisz", "en": "Save"},
    "set.cancel": {"pl": "Anuluj", "en": "Cancel"},
    "set.close": {"pl": "Zamknij", "en": "Close"},
    "set.storage": {"pl": "Katalog danych", "en": "Data folder"},
    "set.open_folder": {"pl": "Otwórz katalog", "en": "Open folder"},
    # --- komunikaty ------------------------------------------------------
    "msg.confirm_new": {
        "pl": "Masz niezapisane zmiany. Kontynuować bez zapisu?",
        "en": "You have unsaved changes. Continue without saving?",
    },
    "msg.confirm_exit": {
        "pl": "Masz niezapisane zmiany. Zamknąć aplikację?",
        "en": "You have unsaved changes. Close the application?",
    },
    "msg.error": {"pl": "Błąd", "en": "Error"},
    "msg.info": {"pl": "Informacja", "en": "Information"},
    "msg.question": {"pl": "Pytanie", "en": "Question"},
    "msg.open_failed": {"pl": "Nie udało się otworzyć pliku: {err}",
                        "en": "Could not open file: {err}"},
    "msg.save_failed": {"pl": "Nie udało się zapisać pliku: {err}",
                        "en": "Could not save file: {err}"},
    "msg.no_selection": {"pl": "Najpierw zaznacz fragment tekstu.",
                         "en": "Select some text first."},
    "msg.file_saved": {"pl": "Zapisano: {path}", "en": "Saved: {path}"},
    "msg.file_opened": {"pl": "Otwarto: {path}", "en": "Opened: {path}"},
    # --- pisownia --------------------------------------------------------
    "tab.spelling": {"pl": "Pisownia", "en": "Spelling"},
    "sp.header": {"pl": "Sprawdzanie pisowni", "en": "Spell checking"},
    "sp.enabled": {"pl": "Sprawdzaj pisownię na bieżąco", "en": "Check spelling as I type"},
    "sp.dictionary": {"pl": "Słownik", "en": "Dictionary"},
    "sp.status": {"pl": "Stan", "en": "Status"},
    "sp.status_ready": {"pl": "gotowy", "en": "ready"},
    "sp.status_loading": {"pl": "wczytywanie…", "en": "loading…"},
    "sp.status_missing": {"pl": "brak słownika", "en": "no dictionary"},
    "sp.status_off": {"pl": "wyłączone", "en": "off"},
    "sp.errors": {"pl": "Błędy", "en": "Errors"},
    "sp.checked": {"pl": "Sprawdzone słowa", "en": "Words checked"},
    "sp.accuracy": {"pl": "Poprawność", "en": "Accuracy"},
    "sp.no_errors": {"pl": "Nie znaleziono błędów pisowni.", "en": "No spelling errors found."},
    "sp.not_ready": {
        "pl": "Zainstaluj słownik dla tego języka, żeby włączyć sprawdzanie pisowni.",
        "en": "Install a dictionary for this language to enable spell checking.",
    },
    "sp.no_engine": {
        "pl": "Brak silnika sprawdzania pisowni (pakiet spylls). Zainstaluj: pip install spylls",
        "en": "Spell-check engine missing (spylls package). Install with: pip install spylls",
    },
    "sp.suggestions": {"pl": "Podpowiedzi", "en": "Suggestions"},
    "sp.searching": {"pl": "Szukam podpowiedzi…", "en": "Looking for suggestions…"},
    "sp.no_suggestions": {"pl": "Brak podpowiedzi", "en": "No suggestions"},
    "sp.add_to_dict": {"pl": "Dodaj do słownika", "en": "Add to dictionary"},
    "sp.ignore": {"pl": "Ignoruj w tej sesji", "en": "Ignore for this session"},
    "sp.replace_all": {"pl": "Zamień wszystkie wystąpienia", "en": "Replace all occurrences"},
    "sp.recheck": {"pl": "Sprawdź ponownie", "en": "Re-check"},
    "sp.hint": {
        "pl": "Kliknij słowo prawym przyciskiem myszy w tekście, żeby zobaczyć podpowiedzi.",
        "en": "Right-click a word in the text to see suggestions.",
    },
    # --- zarzadzanie slownikami ------------------------------------------
    "sp.manage": {"pl": "Słowniki", "en": "Dictionaries"},
    "sp.installed": {"pl": "Zainstalowane", "en": "Installed"},
    "sp.available": {"pl": "Do pobrania", "en": "Available to download"},
    "sp.download": {"pl": "Pobierz", "en": "Download"},
    "sp.downloading": {"pl": "Pobieranie {name}… {pct}%", "en": "Downloading {name}… {pct}%"},
    "sp.downloaded": {"pl": "Pobrano słownik {name}.", "en": "Dictionary {name} downloaded."},
    "sp.download_failed": {"pl": "Nie udało się pobrać słownika: {err}",
                           "en": "Dictionary download failed: {err}"},
    "sp.remove": {"pl": "Usuń", "en": "Remove"},
    "sp.confirm_remove": {"pl": "Usunąć słownik {name} z dysku?",
                          "en": "Remove dictionary {name} from disk?"},
    "sp.import_file": {"pl": "Wgraj z pliku (.oxt / .zip / .dic)",
                       "en": "Install from file (.oxt / .zip / .dic)"},
    "sp.imported": {"pl": "Zainstalowano: {name}", "en": "Installed: {name}"},
    "sp.import_failed": {"pl": "Nie udało się wczytać pliku: {err}",
                         "en": "Could not read the file: {err}"},
    "sp.scan_system": {"pl": "Znajdź słowniki LibreOffice", "en": "Find LibreOffice dictionaries"},
    "sp.scan_found": {"pl": "Znaleziono i zainstalowano: {name}",
                      "en": "Found and installed: {name}"},
    "sp.scan_none": {
        "pl": "Nie znaleziono słowników LibreOffice ani OpenOffice na tym komputerze.",
        "en": "No LibreOffice or OpenOffice dictionaries found on this computer.",
    },
    "sp.links": {"pl": "Strony ze słownikami", "en": "Dictionary download pages"},
    "sp.links_hint": {
        "pl": "Aplikacja używa słowników Hunspell (.dic + .aff) — tych samych co "
              "LibreOffice i FreeOffice. Słownik pobrany dla LibreOffice zadziała tutaj "
              "bez zmian.",
        "en": "The app uses Hunspell dictionaries (.dic + .aff) — the same ones LibreOffice "
              "and FreeOffice use. A dictionary downloaded for LibreOffice works here as is.",
    },
    "sp.open_folder": {"pl": "Otwórz katalog słowników", "en": "Open dictionary folder"},
    "sp.personal": {"pl": "Mój słownik", "en": "My dictionary"},
    "sp.personal_empty": {"pl": "Nie dodano jeszcze żadnych słów.",
                          "en": "No words added yet."},
    "sp.personal_remove": {"pl": "Usuń ze słownika", "en": "Remove from dictionary"},
    "sp.size": {"pl": "rozmiar", "en": "size"},
    "sp.license": {"pl": "licencja", "en": "licence"},
    # --- instrukcja obslugi ----------------------------------------------
    "tb.help": {"pl": "Pomoc", "en": "Help"},
    "help.title": {"pl": "Instrukcja obsługi", "en": "User guide"},
    "help.hint": {
        "pl": "Page Up / Page Down przechodzi między sekcjami. Esc zamyka okno.",
        "en": "Page Up / Page Down moves between sections. Esc closes the window.",
    },
    "help.save": {"pl": "Zapisz jako plik", "en": "Save as file"},
    "help.native": {"pl": "(standardowy skrót systemu)", "en": "(standard system shortcut)"},
    "help.shortcuts_intro": {
        "pl": "Skróty działają w całym oknie programu, także gdy kursor jest w edytorze.",
        "en": "The shortcuts work anywhere in the window, including inside the editor.",
    },
    "help.col_key": {"pl": "Skrót", "en": "Shortcut"},
    "help.col_action": {"pl": "Działanie", "en": "Action"},
    "help.sec.start": {"pl": "Pierwsze kroki", "en": "Getting started"},
    "help.sec.editor": {"pl": "Edytor i sekcje", "en": "Editor and sections"},
    "help.sec.syllables": {"pl": "Sylaby i metryka", "en": "Syllables and meter"},
    "help.sec.rhymes": {"pl": "Rymy", "en": "Rhymes"},
    "help.sec.repetitions": {"pl": "Powtórzenia", "en": "Repetitions"},
    "help.sec.readability": {"pl": "Czytelność", "en": "Readability"},
    "help.sec.spelling": {"pl": "Pisownia", "en": "Spelling"},
    "help.sec.ai": {"pl": "Asystent AI", "en": "AI assistant"},
    "help.sec.export": {"pl": "Eksport", "en": "Export"},
    "help.sec.history": {"pl": "Historia zmian", "en": "Change history"},
    "help.sec.shortcuts": {"pl": "Skróty klawiszowe", "en": "Keyboard shortcuts"},
    "help.sec.files": {"pl": "Pliki i dane", "en": "Files and data"},
    # --- grupy skrotow ---------------------------------------------------
    "key.group.file": {"pl": "Plik", "en": "File"},
    "key.group.edit": {"pl": "Edycja", "en": "Editing"},
    "key.group.sections": {"pl": "Sekcje utworu", "en": "Song sections"},
    "key.group.panels": {"pl": "Panele", "en": "Panels"},
    "key.group.tools": {"pl": "Narzędzia", "en": "Tools"},
    "key.group.view": {"pl": "Widok", "en": "View"},
    "key.group.help": {"pl": "Pomoc", "en": "Help"},
    # --- opisy skrotow ---------------------------------------------------
    "key.new": {"pl": "Nowy utwór", "en": "New song"},
    "key.open": {"pl": "Otwórz plik", "en": "Open file"},
    "key.save": {"pl": "Zapisz", "en": "Save"},
    "key.save_as": {"pl": "Zapisz jako", "en": "Save as"},
    "key.quit": {"pl": "Zamknij program", "en": "Quit"},
    "key.undo": {"pl": "Cofnij", "en": "Undo"},
    "key.redo": {"pl": "Ponów", "en": "Redo"},
    "key.cut": {"pl": "Wytnij", "en": "Cut"},
    "key.copy": {"pl": "Kopiuj", "en": "Copy"},
    "key.paste": {"pl": "Wklej", "en": "Paste"},
    "key.select_all": {"pl": "Zaznacz wszystko", "en": "Select all"},
    "key.context_menu": {
        "pl": "Podpowiedzi pisowni i rymów dla słowa",
        "en": "Spelling suggestions and rhymes for a word",
    },
    "key.section_verse": {"pl": "Wstaw zwrotkę", "en": "Insert a verse"},
    "key.section_chorus": {"pl": "Wstaw refren", "en": "Insert a chorus"},
    "key.section_bridge": {"pl": "Wstaw most", "en": "Insert a bridge"},
    "key.tab_syllables": {"pl": "Panel Sylaby", "en": "Syllables panel"},
    "key.tab_rhymes": {"pl": "Panel Rymy", "en": "Rhymes panel"},
    "key.tab_repetitions": {"pl": "Panel Powtórzenia", "en": "Repetitions panel"},
    "key.tab_readability": {"pl": "Panel Czytelność", "en": "Readability panel"},
    "key.tab_spelling": {"pl": "Panel Pisownia", "en": "Spelling panel"},
    "key.tab_ai": {"pl": "Panel AI", "en": "AI panel"},
    "key.tab_history": {"pl": "Panel Historia", "en": "History panel"},
    "key.tab_export": {"pl": "Panel Eksport", "en": "Export panel"},
    "key.analyze": {"pl": "Przelicz analizę", "en": "Recalculate the analysis"},
    "key.spellcheck": {"pl": "Sprawdź pisownię", "en": "Check spelling"},
    "key.dictionaries": {"pl": "Okno słowników", "en": "Dictionary manager"},
    "key.snapshot": {"pl": "Zapisz punkt w historii", "en": "Save a history snapshot"},
    "key.ai_run": {"pl": "Uruchom zadanie AI", "en": "Run the AI task"},
    "key.ai_stop": {"pl": "Przerwij AI", "en": "Stop the AI"},
    "key.export": {"pl": "Przejdź do eksportu", "en": "Go to export"},
    "key.settings": {"pl": "Ustawienia", "en": "Settings"},
    "key.toggle_theme": {"pl": "Przełącz motyw jasny/ciemny", "en": "Toggle light/dark theme"},
    "key.toggle_text_lang": {"pl": "Przełącz język tekstu PL/EN", "en": "Toggle lyrics language PL/EN"},
    "key.toggle_ui_lang": {"pl": "Przełącz język interfejsu PL/EN", "en": "Toggle UI language PL/EN"},
    "key.font_bigger": {"pl": "Powiększ tekst w edytorze", "en": "Larger editor text"},
    "key.font_smaller": {"pl": "Zmniejsz tekst w edytorze", "en": "Smaller editor text"},
    "key.font_reset": {"pl": "Domyślny rozmiar tekstu", "en": "Default text size"},
    "key.help": {"pl": "Instrukcja obsługi", "en": "User guide"},
    # --- sekcje utworu ---------------------------------------------------
    "list.empty": {"pl": "Brak danych — zacznij pisać.", "en": "No data yet — start writing."},
    "rhy.no_rhymes": {"pl": "Nie wykryto rymów końcowych.", "en": "No end rhymes detected."},
    "rhy.no_candidates": {"pl": "Nie znaleziono rymów. Spróbuj przez AI.",
                          "en": "No rhymes found. Try the AI search."},
    "read.no_hard_lines": {"pl": "Wszystkie wersy mają wygodną długość.",
                           "en": "All lines are a comfortable length."},
    # --- sekcje utworu ---------------------------------------------------
    "sec.intro": {"pl": "Intro", "en": "Intro"},
    "sec.verse": {"pl": "Zwrotka", "en": "Verse"},
    "sec.prechorus": {"pl": "Przedrefren", "en": "Pre-Chorus"},
    "sec.chorus": {"pl": "Refren", "en": "Chorus"},
    "sec.bridge": {"pl": "Most", "en": "Bridge"},
    "sec.outro": {"pl": "Outro", "en": "Outro"},
    "sec.insert": {"pl": "Wstaw sekcję", "en": "Insert section"},
}


def set_ui_language(lang: str) -> None:
    global _current
    if lang not in LANGUAGES:
        lang = "en"
    if lang == _current:
        return
    _current = lang
    for cb in list(_listeners):
        try:
            cb(lang)
        except Exception:  # pragma: no cover - odswiezanie UI nie moze wywrocic apki
            pass


def get_ui_language() -> str:
    return _current


def on_language_change(callback: Callable[[str], None]) -> None:
    _listeners.append(callback)


def tr(key: str, **kwargs) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
