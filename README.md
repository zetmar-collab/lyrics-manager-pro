# Lyrics Manager Pro

Desktopowy warsztat autora tekstów piosenek na Windows. Aplikacja okienkowa
(jeden plik `.exe`, bez instalatora), interfejs po polsku i angielsku, motyw
jasny i ciemny, sprawdzanie pisowni na słownikach Hunspell oraz dwa silniki AI:
**OpenRouter** (chmura) i **Ollama** (lokalnie).

*A desktop workbench for songwriters. Bilingual PL/EN interface, light and dark
theme, Hunspell spell checking, and two AI backends: OpenRouter (cloud) and
Ollama (local).*

---

## Instalacja

Pobierz **LyricsManagerPro-Setup-1.0.0.exe** z sekcji
[Releases](https://github.com/zetmar-collab/lyrics-manager-pro/releases)
i uruchom.

Instalator działa **bez praw administratora** — domyślnie instaluje program
tylko dla Twojego konta. Zakłada skróty w Menu Start i (opcjonalnie) na
pulpicie, kojarzy pliki `.lyr` z programem i dodaje wpis w Panelu sterowania.
Interfejs instalatora jest po polsku i po angielsku.

Nie musisz instalować Pythona ani żadnych bibliotek — aplikacja jest jednym
plikiem wykonywalnym ze wszystkimi modułami w środku.

Wolisz wersję przenośną? Pobierz sam **LyricsManagerPro.exe** z tego samego
miejsca i uruchom z dowolnego katalogu, choćby z pendrive'a.

> Windows może przy pierwszym uruchomieniu pokazać ostrzeżenie SmartScreen,
> bo plik nie jest podpisany certyfikatem wydawcy (kosztuje kilkaset złotych
> rocznie). Kliknij **Więcej informacji → Uruchom mimo to**.

### Odinstalowanie

Panel sterowania → Programy, albo skrót **Dezinstalacja** w Menu Start.
Deinstalator zapyta, czy usunąć także Twoje dane (ustawienia, historię zmian,
słowniki) — domyślnie je zostawia, więc ponowna instalacja niczego nie kasuje.

---

## Uruchomienie i budowanie ze źródeł

**Ze źródeł:**

```bash
pip install -r requirements.txt
python run.py
```

Plik można też przekazać w wierszu polecenia lub upuścić na ikonę programu:

```bash
dist\LyricsManagerPro.exe moj-utwor.lyr
```

**Zbudowanie `.exe` od zera:**

```bash
powershell -ExecutionPolicy Bypass -File build.ps1
```

Skrypt instaluje zależności, generuje ikonę, uruchamia wszystkie testy i buduje
`dist\LyricsManagerPro.exe` (jeden plik, bez konsoli). Rozmiar zalezy od
srodowiska budowania: czysta instalacja Pythona daje ok. 14 MB, komputer
z wieloma pakietami w site-packages nieco wiecej.

**Zbudowanie instalatora:**

```bash
powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
```

Wymaga [Inno Setup 6](https://jrsoftware.org/isdl.php). Skrypt sam znajdzie
kompilator — również wtedy, gdy Inno Setup jest zainstalowany tylko dla
bieżącego użytkownika. Wynik: `dist\LyricsManagerPro-Setup-1.0.0.exe` (ok. 16 MB).

Budowanie jest też zautomatyzowane w GitHub Actions
([.github/workflows/build.yml](.github/workflows/build.yml)) — tag `v*`
tworzy wydanie z obydwoma plikami.

---

## Funkcje

### Licznik sylab
Liczba sylab każdego wersu widoczna w rynnie po lewej stronie edytora, na żywo
podczas pisania. Osobne algorytmy dla polskiego (grupy samogłoskowe z regułą
zmiękczającego „i") i angielskiego (heurystyka z listą wyjątków). Statystyki:
suma, średnia na wers, min/max, **równomierność** wersów (0–100) oraz rozkład
długości i podsumowanie per sekcja utworu.

### Analiza rymów
Wykrywanie rymów końcowych z klasyfikacją: dokładny, niedokładny, asonans,
powtórzenie słowa. Podstawą jest uproszczona transkrypcja fonetyczna — dla
polskiego z dwuznakami (`sz`, `cz`, `rz`, `dzi`…), ubezdźwięcznieniem w wygłosie
i akcentem na przedostatniej sylabie; dla angielskiego z regułami ortograficznymi
(`ough`, `tion`, nieme `e`, `y` jako samogłoska). Dodatkowo:

- schemat rymów (`ABABCCxC`) i gęstość rymowania,
- kolorowanie rymujących się słów wprost w tekście,
- rymy wewnętrzne,
- wyszukiwarka rymów do dowolnego słowa (słownik wbudowany + słowa z Twojego
  tekstu), a gdy to za mało — wyszukiwanie przez AI.

### Wyszukiwanie powtórzeń
Powtarzane słowa, frazy (n-gramy 2–5 słów) i całe wersy, z numerami wersów i
możliwością skoku do miejsca w tekście jednym kliknięciem. Regulowany próg
wystąpień, opcjonalne pomijanie słów funkcyjnych, wskaźnik bogactwa słownictwa.
Powtórzenia są podświetlane w edytorze.

### Ocena czytelności
- **polski:** indeks FOG (adaptacja polska) i indeks Pisarka,
- **angielski:** Flesch Reading Ease i Flesch-Kincaid Grade Level,
- **śpiewalność** (0–100) — miara własna, łącząca równomierność wersów, ich
  długość i udział słów wielosylabowych,
- lista wersów zbyt długich, by wygodnie je zaśpiewać.

### Sprawdzanie pisowni (PL / EN)
Ta sama technologia co w LibreOffice i FreeOffice — słowniki **Hunspell**
(pliki `.dic` + `.aff`). Słownik pobrany kiedyś dla LibreOffice zadziała tutaj
bez żadnych zmian.

- błędy podkreślane na czerwono wprost w tekście, na bieżąco podczas pisania,
- prawy przycisk myszy na słowie → podpowiedzi poprawek, **zamień wszystkie
  wystąpienia**, **dodaj do słownika**, **ignoruj w tej sesji**, a także skrót
  do wyszukiwarki rymów dla tego słowa,
- panel z listą wszystkich błędów, liczbą wystąpień i skokiem do wersu,
- własny słownik autora (nazwy własne, neologizmy, celowe zapisy gwarowe) —
  osobny dla polskiego i angielskiego,
- znaczniki sekcji `[Refren]`, `[Chorus]` są pomijane przy sprawdzaniu.

Dla polskiego to szczególnie przydatne: wyłapuje brakujące znaki diakrytyczne,
czyli najczęstszy błąd przy szybkim pisaniu (`juz` → `już`, `cien` → `cień`).

**Skąd wziąć słowniki.** W panelu *Pisownia* → **Słowniki…** są trzy drogi:

1. **Pobieranie z poziomu aplikacji** — jedno kliknięcie, słownik ląduje
   w `%APPDATA%\LyricsManagerPro\dictionaries`. Dostępne: polski `pl_PL`
   (~5,4 MB), angielski `en_US` (~0,2 MB) i `en_GB` (~0,4 MB). Źródłem jest
   oficjalne repozytorium słowników LibreOffice.
2. **Wgranie z pliku** — jeśli masz już plik `.oxt` (tak dystrybuuje słowniki
   LibreOffice), `.zip` albo parę `.dic` + `.aff`.
3. **Znajdź słowniki LibreOffice** — przeszukuje typowe katalogi instalacyjne
   LibreOffice, OpenOffice i FreeOffice i kopiuje znalezione słowniki.

Strony, z których można pobrać słowniki ręcznie (linki są też klikalne
w oknie *Słowniki…*):

| Język | Adres |
|---|---|
| wszystkie | https://github.com/LibreOffice/dictionaries |
| angielski | https://extensions.libreoffice.org/en/extensions/show/english-dictionaries |
| polski | https://sjp.pl/slownik/ort/ |

Bezpośrednie pliki, których używa przycisk *Pobierz*:

```
https://raw.githubusercontent.com/LibreOffice/dictionaries/master/pl_PL/pl_PL.dic
https://raw.githubusercontent.com/LibreOffice/dictionaries/master/pl_PL/pl_PL.aff
https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_US.dic
https://raw.githubusercontent.com/LibreOffice/dictionaries/master/en/en_US.aff
```

Silnikiem jest [`spylls`](https://pypi.org/project/spylls/) — implementacja
Hunspella w czystym Pythonie, więc `.exe` nie potrzebuje żadnych bibliotek
systemowych. Polski słownik wczytuje się około 3 sekund; dzieje się to w tle,
a panel pokazuje wtedy stan „wczytywanie…".

### Instrukcja obsługi w programie (PL / EN)
Klawisz **F1** albo przycisk **Pomoc** otwiera pełną instrukcję: dwanaście
sekcji opisujących każdą funkcję, z osobnym rozdziałem na skróty klawiszowe.
Treść jest napisana od zera w obu językach — nie jest tłumaczeniem maszynowym —
i przełącza się razem z językiem interfejsu.

Instrukcję można zapisać do pliku Markdown (przycisk **Zapisz jako plik**),
żeby wydrukować albo trzymać poza programem.

### AI — alternatywne wersje i nie tylko
Jedenaście zadań: alternatywne wersje fragmentu, propozycje rymów, dopisanie
dalszego ciągu, dopracowanie języka, wzbogacenie obrazowania, uproszczenie,
dopasowanie liczby sylab, śpiewalne tłumaczenie, propozycje tytułów, recenzja
tekstu i budowa promptu stylu dla Suno/Udio.

Prompt zawiera kontekst utworu: tytuł, styl, wykryty schemat rymów i liczbę
sylab w kolejnych wersach — model wie, w jakie ramy metryczne ma trafić.

Odpowiedź spływa strumieniowo i można ją w każdej chwili przerwać, a potem
wstawić do tekstu, zastąpić nią zakres albo skopiować.

### Eksport do Suno i Udio
Automatyczne rozpoznanie i normalizacja znaczników sekcji — `[Zwrotka 1]` staje
się `[Verse 1]`, `[Refren]` → `[Chorus]`. Jeśli w tekście nie ma znaczników,
aplikacja rozpozna bloki: powtarzający się blok oznaczy jako `[Chorus]`,
pozostałe jako kolejne `[Verse]`. Do tego pole „Style of Music" budowane z
metryczki utworu i kontrola limitu znaków (Suno 5000, Udio 4000).

Poza tym eksport do czystego tekstu oraz do Markdown z pełnym raportem
analitycznym (metryka, rymy, powtórzenia, czytelność).

### Historia zmian
Migawki tekstu w bazie SQLite: ręczne (z własnym opisem) i automatyczne — co
zadany czas, przy zapisie, otwarciu nowego utworu i przy zamykaniu aplikacji.
Dla każdej migawki: podgląd, kolorowany diff wobec bieżącego tekstu z licznikiem
zmienionych wersów, przywracanie (z zabezpieczającą migawką stanu bieżącego)
i usuwanie.

---

## Dwa języki, dwa niezależne przełączniki

- **Język UI** — cały interfejs po polsku albo po angielsku, przełączany w locie.
- **Język tekstu** — decyduje, którego algorytmu użyć do liczenia sylab, rymów
  i czytelności, oraz którego słownika użyć przy sprawdzaniu pisowni.
- **Język odpowiedzi AI** — ustawiany osobno w panelu AI.

Można więc pisać po polsku, mieć interfejs po angielsku i prosić AI o recenzję
po polsku — te trzy ustawienia nie są ze sobą związane.

---

## Konfiguracja silników AI

### Ollama (lokalnie, bez wysyłania tekstu w świat)

```bash
ollama serve
ollama pull llama3.1
```

W **Ustawieniach → Silniki AI** wskaż adres serwera (domyślnie
`http://localhost:11434`) i model. Przycisk **Testuj połączenie** sprawdzi,
czy wszystko działa. Lista modeli pobiera się automatycznie.

### OpenRouter (chmura)

Klucz API z [openrouter.ai/keys](https://openrouter.ai/keys) wpisz w
**Ustawieniach → Silniki AI**. Jest zapisywany lokalnie w pliku ustawień na
tym komputerze — nie jest nigdzie wysyłany poza samo API OpenRoutera.
Lista dostępnych modeli pobiera się z serwera.

---

## Skróty klawiszowe

Pełną listę znajdziesz też w programie: **F1 → Skróty klawiszowe**,
skąd można ją zapisać do pliku.

**Plik**

| Skrót | Działanie |
|---|---|
| `Ctrl+N` | Nowy utwór |
| `Ctrl+O` | Otwórz plik |
| `Ctrl+S` | Zapisz |
| `Ctrl+Shift+S` | Zapisz jako |
| `Ctrl+Q` | Zamknij program |

**Edycja**

| Skrót | Działanie |
|---|---|
| `Ctrl+Z` | Cofnij *(standardowy skrót systemu)* |
| `Ctrl+Y` | Ponów *(standardowy skrót systemu)* |
| `Ctrl+X` | Wytnij *(standardowy skrót systemu)* |
| `Ctrl+C` | Kopiuj *(standardowy skrót systemu)* |
| `Ctrl+V` | Wklej *(standardowy skrót systemu)* |
| `Ctrl+A` | Zaznacz wszystko *(standardowy skrót systemu)* |
| `Prawy przycisk myszy` | Podpowiedzi pisowni i rymów dla słowa *(standardowy skrót systemu)* |

**Sekcje utworu**

| Skrót | Działanie |
|---|---|
| `Ctrl+Shift+V` | Wstaw zwrotkę |
| `Ctrl+Shift+C` | Wstaw refren |
| `Ctrl+Shift+B` | Wstaw most |

**Panele**

| Skrót | Działanie |
|---|---|
| `Alt+1` | Panel Sylaby |
| `Alt+2` | Panel Rymy |
| `Alt+3` | Panel Powtórzenia |
| `Alt+4` | Panel Czytelność |
| `Alt+5` | Panel Pisownia |
| `Alt+6` | Panel AI |
| `Alt+7` | Panel Historia |
| `Alt+8` | Panel Eksport |

**Narzędzia**

| Skrót | Działanie |
|---|---|
| `F5` | Przelicz analizę |
| `F7` | Sprawdź pisownię |
| `Ctrl+Shift+D` | Okno słowników |
| `Ctrl+Shift+H` | Zapisz punkt w historii |
| `Ctrl+Enter` | Uruchom zadanie AI |
| `Esc` | Przerwij AI |
| `Ctrl+E` | Przejdź do eksportu |
| `Ctrl+,` | Ustawienia |

**Widok**

| Skrót | Działanie |
|---|---|
| `Ctrl+T` | Przełącz motyw jasny/ciemny |
| `Ctrl+L` | Przełącz język tekstu PL/EN |
| `Ctrl+Shift+L` | Przełącz język interfejsu PL/EN |
| `Ctrl++` | Powiększ tekst w edytorze |
| `Ctrl+-` | Zmniejsz tekst w edytorze |
| `Ctrl+0` | Domyślny rozmiar tekstu |

**Pomoc**

| Skrót | Działanie |
|---|---|
| `F1` | Instrukcja obsługi |

---

## Gdzie trzymane są dane

`%APPDATA%\LyricsManagerPro\`

- `settings.json` — ustawienia i klucz API,
- `history.db` — historia zmian (SQLite),
- `personal_dictionary.json` — Twoje własne słowa dla sprawdzania pisowni,
- `dictionaries\` — słowniki Hunspell (`.dic` + `.aff`).

Utwory zapisują się tam, gdzie wskażesz, w formacie `.lyr` (JSON: tekst +
metryczka). Aplikacja otworzy też zwykłe `.txt` i `.md`.

---

## Struktura projektu

```
lyrics_manager/
  analysis/          liczenie sylab, fonetyka, rymy, powtórzenia, czytelność
  ai/                silniki (OpenRouter, Ollama) i budowanie promptów
  ui/                okno główne, edytor, panele, ustawienia, motywy
  i18n.py            wszystkie napisy PL/EN
  shortcuts.py       tabela skrótów — źródło dla okna i dla instrukcji
  help_content.py    treść instrukcji obsługi PL/EN
  spelling.py        słowniki Hunspell, pobieranie, słownik użytkownika
  config.py          ustawienia w %APPDATA%
  document.py        model utworu i pliki .lyr
  export.py          Suno, Udio, tekst, Markdown
  history.py         migawki SQLite i diff
tests/
  test_analysis.py   testy modułów analitycznych
  test_spelling.py   testy sprawdzania pisowni i katalogu słowników
  test_shortcuts_help.py  testy skrótów, kolizji z Tk i instrukcji obsługi
  test_ui_smoke.py   test dymny interfejsu (buduje i zamyka okno bez udziału użytkownika)
tools/make_icon.py   generowanie assets/app.ico
installer/
  LyricsManagerPro.iss  skrypt instalatora (Inno Setup)
  build_installer.ps1   budowanie instalatora
  info_before.txt       tekst powitalny instalatora PL/EN
LyricsManagerPro.spec konfiguracja PyInstallera
build.ps1            pełny build: zależności → ikona → testy → .exe
```

## Testy

```bash
python tests\test_analysis.py
python tests\test_spelling.py
python tests\test_shortcuts_help.py
python tests\test_ui_smoke.py
```

Pierwszy sprawdza liczenie sylab (PL i EN), klasyfikację rymów, wykrywanie
powtórzeń, metryki czytelności, eksport i zapis/odczyt dokumentu. Drugi —
sprawdzanie pisowni, słownik użytkownika i import archiwum `.oxt` (testy
wymagające prawdziwych słowników pomijają się z komunikatem, gdy słowników
nie ma). Trzeci — spójność tabeli skrótów, kompletność tłumaczeń, faktyczne
przypisanie skrótów w oknie oraz to, że skróty kolidujące z wbudowanymi
skrótami Tk (`Ctrl+K`, `Ctrl+T`) nie zmieniają tekstu; sprawdza też każdą
sekcję instrukcji i jej eksport do pliku w obu językach. Czwarty buduje całe
okno, przechodzi przez wszystkie zakładki, otwiera okno słowników i menu
kontekstowe, przełącza język i motyw, po czym zamyka aplikację — bez udziału
użytkownika.

Diagnostyka gotowego `.exe` (zapisuje raport o zależnościach i słownikach):

```bash
dist\LyricsManagerPro.exe --selftest raport.txt
```

## Wymagania

Windows 10/11. Gotowy `.exe` nie wymaga Pythona ani żadnych bibliotek
systemowych. Do budowania ze źródeł: Python 3.10+, `customtkinter`, `requests`,
`spylls`, `pyinstaller`, `pillow`.

Uwaga przy uruchamianiu ze źródeł pod Pythonem ze Sklepu Windows: ta wersja
Pythona działa w kontenerze i przekierowuje zapisy do `%APPDATA%` na
`%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python…\LocalCache\Roaming`.
Ustawienia i słowniki zapisane przy uruchomieniu ze źródeł nie będą wtedy
widoczne dla `.exe` i odwrotnie.

---

## Licencja

Kod na licencji [MIT](LICENSE) — możesz go używać, zmieniać i rozpowszechniać,
także komercyjnie, zachowując informację o autorstwie.

Program korzysta z bibliotek CustomTkinter (MIT), requests (Apache 2.0)
i spylls (MIT) — pełna lista w [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Słowniki pisowni nie są częścią programu — pobierane są na
żądanie z repozytorium LibreOffice i pozostają na swoich licencjach.

## Autor

Marek Zettel — [github.com/zetmar-collab](https://github.com/zetmar-collab)
