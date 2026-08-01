"""Tresc instrukcji obslugi w wersji polskiej i angielskiej.

Prosty format tekstowy renderowany w oknie pomocy:
    "# tytul"    - naglowek sekcji
    "## tytul"   - podnaglowek
    "- punkt"    - punkt listy
    "  wciecie"  - tekst zalezny od punktu wyzej
    "> uwaga"    - wyrozniona uwaga
    pusty wiersz - odstep
"""

from __future__ import annotations

# Klucze sekcji w kolejnosci wyswietlania. Tytuly beda tlumaczone przez i18n
# ("help.sec.<klucz>"), tresc pochodzi z ponizszego slownika.
SECTION_KEYS = [
    "start", "editor", "syllables", "rhymes", "repetitions", "readability",
    "spelling", "ai", "export", "history", "shortcuts", "files",
]

CONTENT: dict[str, dict[str, str]] = {

# =========================================================================
"start": {"pl": """
# Pierwsze kroki

Lyrics Manager Pro to edytor tekstów piosenek, który na bieżąco liczy sylaby,
wykrywa rymy i powtórzenia, sprawdza pisownię i pozwala poprosić AI o pomoc.

## Układ okna

- **Górny pasek** — plik, wstawianie sekcji, języki, motyw, ustawienia.
- **Metryczka** — tytuł, wykonawca, styl, tempo i tonacja. Styl trafia do
  eksportu jako opis dla Suno i Udio, więc warto go wypełnić.
- **Edytor** (po lewej) — tu piszesz. Wąska kolumna po lewej stronie edytora
  to licznik sylab dla każdego wersu.
- **Panele** (po prawej) — osiem zakładek z analizą, AI, historią i eksportem.
- **Pasek stanu** (na dole) — komunikaty, nazwa pliku i znacznik niezapisanych
  zmian.

## Trzy niezależne przełączniki języka

To najczęstsze źródło nieporozumień, więc po kolei:

- **Język UI** — język napisów w programie.
- **Język tekstu** — którym algorytmem liczyć sylaby, rymy i czytelność oraz
  którego słownika użyć przy pisowni. Ustaw go zgodnie z językiem piosenki.
- **Język odpowiedzi AI** — w panelu AI, osobno.

Możesz więc pisać po polsku, mieć interfejs po angielsku i dostawać recenzję
od AI po polsku. Te ustawienia nie są ze sobą związane.

## Zaczynamy

1. Wpisz tytuł w metryczce.
2. Ustaw **Język tekstu** na język piosenki.
3. Pisz. Liczby po lewej pokazują sylaby, rymujące się słowa kolorują się same.
4. Zapisz przez **Ctrl+S** — powstanie plik `.lyr` z tekstem i metryczką.
""", "en": """
# Getting started

Lyrics Manager Pro is a lyrics editor that counts syllables as you type,
detects rhymes and repetitions, checks spelling, and lets you ask an AI
for help.

## Window layout

- **Top bar** — file actions, section insert, languages, theme, settings.
- **Metadata row** — title, artist, style, tempo and key. The style feeds the
  Suno and Udio export prompt, so it is worth filling in.
- **Editor** (left) — where you write. The narrow column on its left is the
  syllable count for each line.
- **Panels** (right) — eight tabs with analysis, AI, history and export.
- **Status bar** (bottom) — messages, file name and the unsaved-changes marker.

## Three independent language switches

This is the most common point of confusion, so in order:

- **UI language** — the language of the program's labels.
- **Lyrics language** — which algorithm counts syllables, rhymes and
  readability, and which dictionary spell checking uses. Set it to the
  language of the song.
- **AI output language** — set separately in the AI panel.

So you can write in Polish, keep the interface in English, and get the AI's
critique in Polish. These settings are not tied together.

## Let's start

1. Type a title in the metadata row.
2. Set **Lyrics language** to the language of the song.
3. Write. The numbers on the left show syllables; rhyming words colour
   themselves.
4. Save with **Ctrl+S** — you get a `.lyr` file with the lyrics and metadata.
"""},

# =========================================================================
"editor": {"pl": """
# Edytor i sekcje

## Znaczniki sekcji

Sekcje zapisuje się w nawiasach kwadratowych na osobnym wersie:

    [Zwrotka 1]
    [Refren]
    [Most]

Program rozpoznaje je automatycznie: nie liczy ich sylab, koloruje na fioletowo
i pokazuje w rynnie znak §. W statystykach dostajesz podsumowanie każdej sekcji
osobno.

Sekcję wstawisz z listy **Wstaw sekcję** na górnym pasku albo skrótem:
**Ctrl+Shift+V** (zwrotka), **Ctrl+Shift+C** (refren), **Ctrl+Shift+B** (most).

> Polskie i angielskie nazwy sekcji działają tak samo. Przy eksporcie do Suno
> i Udio polskie są automatycznie tłumaczone na angielskie, bo tego oczekują
> te serwisy.

## Rynna z licznikiem sylab

Liczby po lewej to sylaby w wersie. Wersy wyraźnie dłuższe od średniej
zmieniają kolor na bursztynowy — to sygnał, że mogą się źle śpiewać.

Rynnę można wyłączyć w **Ustawieniach → Edytor**.

## Menu podręczne

Prawy przycisk myszy na słowie daje: podpowiedzi pisowni, zamianę wszystkich
wystąpień, dodanie słowa do własnego słownika oraz szukanie rymów do tego
słowa.

## Rozmiar tekstu

**Ctrl++** i **Ctrl+-** zmieniają rozmiar czcionki edytora, **Ctrl+0**
przywraca domyślny.
""", "en": """
# Editor and sections

## Section markers

Sections go in square brackets on their own line:

    [Verse 1]
    [Chorus]
    [Bridge]

The program recognises them automatically: it does not count their syllables,
colours them purple, and shows a § in the gutter. Statistics include a summary
for each section separately.

Insert a section from the **Insert section** dropdown in the top bar, or with
**Ctrl+Shift+V** (verse), **Ctrl+Shift+C** (chorus), **Ctrl+Shift+B** (bridge).

> Polish and English section names both work. On export to Suno and Udio the
> Polish ones are translated to English automatically, because that is what
> those services expect.

## The syllable gutter

The numbers on the left are syllables per line. Lines clearly longer than the
average turn amber — a hint that they may be awkward to sing.

You can turn the gutter off in **Settings → Editor**.

## Context menu

Right-click a word for spelling suggestions, replace-all, adding the word to
your personal dictionary, and a rhyme search for that word.

## Text size

**Ctrl++** and **Ctrl+-** change the editor font size, **Ctrl+0** restores the
default.
"""},

# =========================================================================
"syllables": {"pl": """
# Sylaby i metryka

## Jak liczone są sylaby

- **Polski** — sylaba to grupa samogłosek. Uwzględniona jest reguła
  zmiękczającego „i": „ziemia" to 2 sylaby, nie 3, bo „i" przed samogłoską
  jedynie zmiękcza spółgłoskę.
- **Angielski** — heurystyka: grupy samogłosek, nieme końcowe „e", końcówki
  „-ed" i „-es", plus lista wyjątków („fire", „beautiful", „every").

## Co pokazuje panel

- **Sylaby razem**, **średnio na wers**, **min/maks**.
- **Równomierność** (0–100) — jak bardzo wersy są do siebie podobne długością.
  Wysoka wartość oznacza regularną metrykę, łatwą do zaśpiewania w stałym
  rytmie. Niska nie jest błędem, ale warto wiedzieć, że tak jest.
- **Rozkład długości wersów** — ile wersów ma ile sylab.
- **Sekcje utworu** — średnia długość wersu w każdej sekcji. Refren zwykle
  bywa krótszy od zwrotki; jeśli jest odwrotnie, warto się zastanowić.

> Kliknięcie sekcji na liście przenosi kursor do tego miejsca w tekście.
""", "en": """
# Syllables and meter

## How syllables are counted

- **Polish** — a syllable is a vowel group, with the softening "i" rule
  applied: "ziemia" is 2 syllables, not 3, because "i" before a vowel only
  palatalises the preceding consonant.
- **English** — a heuristic: vowel groups, silent final "e", the "-ed" and
  "-es" endings, plus an exception list ("fire", "beautiful", "every").

## What the panel shows

- **Total syllables**, **average per line**, **min/max**.
- **Evenness** (0–100) — how similar the lines are in length. A high value
  means a regular meter that is easy to sing to a steady rhythm. A low value
  is not an error, but it is worth knowing.
- **Line length distribution** — how many lines have how many syllables.
- **Song sections** — average line length per section. A chorus is usually
  shorter than a verse; if it is the other way round, it is worth a thought.

> Clicking a section in the list moves the cursor to that place in the text.
"""},

# =========================================================================
"rhymes": {"pl": """
# Rymy

## Klasyfikacja

Program porównuje zakończenia wyrazów po uproszczonej transkrypcji fonetycznej
i dzieli rymy na cztery rodzaje:

- **dokładny** — „tyłu / pyłu", „nocą / mocą",
- **niedokładny** — zgadza się samogłoska i większość zakończenia,
  np. „serce / wierzce",
- **asonans** — zgadzają się tylko samogłoski, np. „droga / trzyma",
- **powtórzenie słowa** — ten sam wyraz na końcu dwóch wersów.

Dla polskiego uwzględniane są dwuznaki (sz, cz, rz, dzi), ubezdźwięcznienie
w wygłosie („chleb" brzmi jak „chlep") oraz akcent na przedostatniej sylabie.
Dla angielskiego — typowe reguły ortograficzne (ough, tion, nieme „e").

## Schemat rymów

Ciąg liter typu `ABABCCxC`. Każda litera to jedna grupa rymowa, `x` oznacza
wers bez rymu. To najszybszy sposób, żeby zobaczyć, czy utwór trzyma się
jednego wzoru.

## Gęstość rymów

Procent wersów objętych jakimkolwiek rymem. Nie ma tu jednej dobrej wartości —
ballada może mieć 50%, rap 100%. Liczy się to, czy wynik zgadza się z Twoim
zamiarem.

## Wyszukiwarka rymów

Wpisz słowo i naciśnij **Szukaj**. Program przeszuka wbudowany słownik i słowa
z Twojego tekstu (te są oznaczone kropką). Kliknięcie propozycji wstawia ją
w miejsce kursora.

Jeśli propozycji jest za mało, **Poszukaj rymów przez AI** przekaże słowo do
modelu razem z kontekstem utworu — dostaniesz też rymy składane i gotowe wersy.

> Podświetlanie rymów w tekście można wyłączyć polem wyboru w panelu.
""", "en": """
# Rhymes

## Classification

The program compares word endings after a simplified phonetic transcription
and sorts rhymes into four kinds:

- **perfect** — "night / light", "rain / pain",
- **slant** — the vowel and most of the ending match, e.g. "heart / start",
- **assonance** — only the vowels match,
- **same word** — the identical word ends two lines.

For Polish it accounts for digraphs (sz, cz, rz, dzi), final devoicing, and
penultimate stress. For English — the usual orthographic rules (ough, tion,
silent "e").

## Rhyme scheme

A string like `ABABCCxC`. Each letter is one rhyme group, `x` marks an
unrhymed line. It is the fastest way to see whether the song keeps to a
single pattern.

## Rhyme density

The percentage of lines covered by any rhyme. There is no single right
number — a ballad may sit at 50%, a rap at 100%. What matters is whether the
figure matches your intent.

## Rhyme finder

Type a word and press **Search**. The program searches its built-in word list
and the words in your own text (those are marked with a dot). Clicking a
suggestion inserts it at the cursor.

If that is not enough, **Find rhymes with AI** sends the word to the model
along with the song's context — you also get compound rhymes and ready-made
lines.

> Rhyme highlighting in the text can be switched off with the checkbox in the
> panel.
"""},

# =========================================================================
"repetitions": {"pl": """
# Powtórzenia

Panel pokazuje trzy poziomy powtórzeń:

- **powtarzane wersy** — całe identyczne wersy,
- **powtarzane frazy** — od 2 do 5 słów pod rząd,
- **powtarzane słowa** — pojedyncze wyrazy.

Wszystko z numerami wersów; kliknięcie przenosi do tego miejsca w tekście.
Znalezione słowa są dodatkowo podświetlane na żółto w edytorze (tylko gdy ta
zakładka jest otwarta).

## Ustawienia

- **Minimalna liczba wystąpień** — od ilu powtórzeń zgłaszać.
- **Pomijaj słowa funkcyjne** — nie zgłaszaj „i", „w", „na", „the", „a".
  Zwykle warto to zostawić włączone.

## Bogactwo słownictwa

Procent słów unikalnych w całym tekście. Niska wartość w refrenie jest
naturalna i pożądana — refren ma się wbijać w pamięć. Niska wartość
w zwrotkach oznacza zwykle, że tekst się kręci w kółko.

> Powtórzenie to narzędzie, nie błąd. Panel ma Ci pokazać, gdzie ono jest,
> a nie kazać je usuwać.
""", "en": """
# Repetitions

The panel shows three levels of repetition:

- **repeated lines** — whole identical lines,
- **repeated phrases** — 2 to 5 words in a row,
- **repeated words** — single words.

All with line numbers; clicking jumps to that place in the text. Found words
are also highlighted in yellow in the editor (only while this tab is open).

## Settings

- **Minimum occurrences** — from how many repeats to report.
- **Ignore function words** — do not report "the", "a", "in", "i", "w".
  Usually worth leaving on.

## Lexical diversity

The percentage of unique words in the whole text. A low value in a chorus is
natural and desirable — a chorus is meant to stick. A low value across the
verses usually means the lyrics are going in circles.

> Repetition is a tool, not a mistake. The panel is there to show you where it
> is, not to tell you to remove it.
"""},

# =========================================================================
"readability": {"pl": """
# Czytelność i śpiewalność

## Wskaźniki

- **Polski** — indeks FOG (adaptacja polska) i indeks Pisarka. Oba mówią,
  ilu lat nauki wymaga swobodne zrozumienie tekstu.
- **Angielski** — Flesch Reading Ease (0–100, im wyżej tym łatwiej) oraz
  Flesch-Kincaid Grade Level.
- **Wynik ogólny** (0–100) — przeliczenie powyższych na jedną skalę.

## Śpiewalność

Wskaźnik własny programu, liczony z trzech składników:

- równomierności długości wersów,
- średniej długości wersu (optimum to 6–12 sylab),
- udziału słów długich, czterosylabowych i dłuższych.

Wysoka śpiewalność oznacza tekst, który łatwo ułożyć w ustach i zapamiętać.

## Na co celować

Dla tekstów piosenek dobry przedział to **60–90**. Poniżej 45 tekst zaczyna
być trudny w odbiorze ze słuchu — a piosenki słucha się raz, bez możliwości
cofnięcia wzrokiem.

Lista **wersów trudnych do zaśpiewania** zbiera te, które znacznie odstają
długością od reszty.

> To są wskazówki, nie oceny. Tekst ambitny, gęsty od metafor, z założenia
> będzie miał niższy wynik i nie ma w tym nic złego.
""", "en": """
# Readability and singability

## Metrics

- **Polish** — the FOG index (Polish adaptation) and the Pisarek index. Both
  express how many years of schooling comfortable comprehension needs.
- **English** — Flesch Reading Ease (0–100, higher is easier) and the
  Flesch-Kincaid Grade Level.
- **Overall score** (0–100) — the above mapped onto a single scale.

## Singability

The program's own measure, built from three parts:

- how even the line lengths are,
- the average line length (6–12 syllables is the sweet spot),
- the share of long words, four syllables and up.

High singability means lyrics that sit easily in the mouth and stick in the
memory.

## What to aim for

For song lyrics, **60–90** is a good range. Below 45 the text starts to be
hard to take in by ear — and a song is heard once, with no way to look back.

The **hard-to-sing lines** list collects the lines that stand out in length.

> These are hints, not verdicts. Ambitious lyrics, dense with metaphor, will
> score lower by design, and there is nothing wrong with that.
"""},

# =========================================================================
"spelling": {"pl": """
# Pisownia

Program używa słowników **Hunspell** (pliki `.dic` + `.aff`) — dokładnie tych
samych co LibreOffice i FreeOffice. Słownik pobrany kiedyś dla LibreOffice
zadziała tutaj bez żadnych zmian.

## Jak z tego korzystać

Błędy są podkreślane na czerwono w tekście, na bieżąco. Prawy przycisk myszy
na podkreślonym słowie daje:

- listę podpowiedzi — kliknięcie poprawia słowo,
- **zamień wszystkie wystąpienia** — poprawia je w całym tekście naraz,
- **dodaj do słownika** — jeśli słowo jest poprawne (nazwa własna, neologizm,
  celowy zapis gwarowy),
- **ignoruj w tej sesji** — nie zgłaszaj do zamknięcia programu.

Panel **Pisownia** zbiera wszystkie błędy w jedną listę z liczbą wystąpień
i skokiem do wersu.

> Dla polskiego najczęściej wyłapuje brakujące znaki diakrytyczne — „juz"
> zamiast „już", „cien" zamiast „cień". To najczęstszy błąd przy szybkim
> pisaniu.

## Skąd wziąć słownik

Panel **Pisownia** → przycisk **Słowniki…**. Trzy drogi:

1. **Pobierz** — jedno kliknięcie, program ściągnie słownik z oficjalnego
   repozytorium LibreOffice. Dostępne: polski (pl_PL, ok. 5,4 MB), angielski
   amerykański (en_US) i brytyjski (en_GB).
2. **Wgraj z pliku** — jeśli masz już plik `.oxt` (tak dystrybuuje słowniki
   LibreOffice), `.zip` albo parę `.dic` + `.aff`.
3. **Znajdź słowniki LibreOffice** — przeszuka katalogi instalacyjne
   LibreOffice, OpenOffice i FreeOffice i skopiuje, co znajdzie.

W tym samym oknie są klikalne odnośniki do stron ze słownikami:
github.com/LibreOffice/dictionaries, extensions.libreoffice.org oraz sjp.pl.

## Uwagi

- Polski słownik wczytuje się około 3 sekund przy pierwszym użyciu. Dzieje się
  to w tle, panel pokazuje wtedy „wczytywanie…".
- Znaczniki sekcji `[Refren]` nie są sprawdzane.
- Słownik dobierany jest według **języka tekstu**, nie języka interfejsu.
- Własne słowa są zapisywane osobno dla polskiego i angielskiego.
""", "en": """
# Spelling

The program uses **Hunspell** dictionaries (`.dic` + `.aff` files) — exactly
the same ones LibreOffice and FreeOffice use. A dictionary you once downloaded
for LibreOffice works here unchanged.

## How to use it

Errors are underlined in red as you type. Right-clicking an underlined word
gives you:

- a list of suggestions — click one to fix the word,
- **replace all occurrences** — fixes it throughout the text at once,
- **add to dictionary** — if the word is correct (a proper noun, a coinage,
  a deliberate dialect spelling),
- **ignore for this session** — stop reporting it until the program closes.

The **Spelling** panel collects every error into one list with occurrence
counts and jump-to-line.

> For Polish it mostly catches missing diacritics — "juz" instead of "już",
> "cien" instead of "cień". That is the most common slip when typing fast.

## Where to get a dictionary

The **Spelling** panel → **Dictionaries…** button. Three routes:

1. **Download** — one click and the program fetches the dictionary from the
   official LibreOffice repository. Available: Polish (pl_PL, about 5.4 MB),
   American English (en_US) and British English (en_GB).
2. **Install from file** — if you already have an `.oxt` file (that is how
   LibreOffice ships dictionaries), a `.zip`, or a `.dic` + `.aff` pair.
3. **Find LibreOffice dictionaries** — scans the LibreOffice, OpenOffice and
   FreeOffice install folders and copies whatever it finds.

The same window has clickable links to dictionary pages:
github.com/LibreOffice/dictionaries, extensions.libreoffice.org and sjp.pl.

## Notes

- The Polish dictionary takes about 3 seconds to load the first time. It loads
  in the background; the panel shows "loading…" meanwhile.
- Section markers like `[Chorus]` are not checked.
- The dictionary is picked by **lyrics language**, not by the interface
  language.
- Your own words are stored separately for Polish and English.
"""},

# =========================================================================
"ai": {"pl": """
# Asystent AI

## Dwa silniki

- **Ollama (lokalnie)** — modele działają na Twoim komputerze. Tekst nigdzie
  nie wychodzi. Wymaga zainstalowanej Ollamy i pobranego modelu:

      ollama serve
      ollama pull llama3.1

- **OpenRouter (chmura)** — dostęp do modeli komercyjnych przez jedno API.
  Wymaga klucza z openrouter.ai/keys, który wpisujesz w
  **Ustawieniach → Silniki AI**. Klucz jest zapisywany tylko na tym
  komputerze.

Lista modeli pobiera się sama; przycisk ⟳ odświeża ją ręcznie. W ustawieniach
jest też **Testuj połączenie**, który od razu powie, czy wszystko działa.

## Zadania

| Zadanie | Do czego służy |
|---|---|
| Alternatywne wersje | 4 warianty fragmentu o różnym charakterze |
| Propozycje rymów | rymy dokładne, niedokładne i składane + gotowe wersy |
| Dopisz dalszy ciąg | około 8 wersów w tym samym nastroju i metrum |
| Dopracuj język | usuwa watę słowną, poprawia akcenty |
| Wzbogać obrazowanie | zamienia abstrakcje na konkret zmysłowy |
| Uprość i skróć | krótsze słowa i wersy, łatwiej zapamiętać |
| Dopasuj liczbę sylab | wyrównuje wersy do zadanej długości |
| Przetłumacz śpiewalnie | przekład z zachowaniem sylab i rymów |
| Zaproponuj tytuły | 10 propozycji z uzasadnieniem |
| Recenzja tekstu | szczera opinia redaktora |
| Zbuduj prompt stylu | opis stylu do Suno lub Udio |

## Zakres i kontekst

**Zakres** decyduje, czy AI pracuje na zaznaczeniu, czy na całym tekście.
Niezależnie od tego model dostaje w promptcie kontekst utworu: tytuł, styl,
wykryty schemat rymów i liczbę sylab w kolejnych wersach — dzięki temu wie,
w jakie ramy metryczne ma trafić.

W polu **Dodatkowe wskazówki** możesz dopisać własne wymagania, na przykład
„zachowaj 8 sylab w wersie, ton nostalgiczny, bez rymów gramatycznych".

**Kreatywność** to temperatura modelu: niżej — bezpieczniej i bliżej
oryginału, wyżej — odważniej i bardziej nieprzewidywalnie.

## Praca z wynikiem

Odpowiedź spływa strumieniowo i można ją przerwać (**Esc**). Potem:
**Wstaw do tekstu** dopisuje ją w miejscu kursora, **Zastąp zakres** podmienia
to, na czym AI pracowało, **Kopiuj** przenosi do schowka.

> AI nie zapisuje niczego samo. Dopóki nie klikniesz „Wstaw" albo „Zastąp",
> Twój tekst pozostaje nietknięty.
""", "en": """
# AI assistant

## Two engines

- **Ollama (local)** — models run on your own computer. The text never leaves
  it. Requires Ollama installed and a model pulled:

      ollama serve
      ollama pull llama3.1

- **OpenRouter (cloud)** — access to commercial models through one API.
  Requires a key from openrouter.ai/keys, entered in
  **Settings → AI engines**. The key is stored on this computer only.

The model list loads by itself; the ⟳ button refreshes it. Settings also has
**Test connection**, which tells you straight away whether it works.

## Tasks

| Task | What it does |
|---|---|
| Alternative versions | 4 variants of the passage, each with a different angle |
| Rhyme suggestions | perfect, slant and compound rhymes + ready-made lines |
| Continue the lyrics | about 8 lines in the same mood and meter |
| Polish the language | cuts filler, fixes stress placement |
| Enrich imagery | swaps abstractions for concrete sensory detail |
| Simplify and shorten | shorter words and lines, easier to remember |
| Fit syllable count | levels the lines to a target length |
| Singable translation | a translation that keeps syllables and rhymes |
| Suggest titles | 10 options with reasoning |
| Critique the lyrics | an honest editor's opinion |
| Build a style prompt | a style description for Suno or Udio |

## Scope and context

**Scope** decides whether the AI works on the selection or the whole text.
Either way the model receives the song's context in the prompt: title, style,
the detected rhyme scheme and the syllable count of each line — so it knows
what metrical frame to hit.

In **Extra instructions** you can add your own requirements, for example
"keep 8 syllables per line, nostalgic tone, no grammatical rhymes".

**Creativity** is the model's temperature: lower means safer and closer to the
original, higher means bolder and less predictable.

## Working with the result

The answer streams in and can be interrupted (**Esc**). Then:
**Insert into text** adds it at the cursor, **Replace scope** swaps out what
the AI worked on, **Copy** puts it on the clipboard.

> The AI never writes anything on its own. Until you click "Insert" or
> "Replace", your text stays untouched.
"""},

# =========================================================================
"export": {"pl": """
# Eksport

## Suno i Udio

Program przygotowuje tekst w formacie, którego oczekują generatory muzyki AI:

- **znaczniki sekcji** są normalizowane — `[Zwrotka 1]` staje się `[Verse 1]`,
  `[Refren]` → `[Chorus]`, `[Most]` → `[Bridge]`;
- jeśli w tekście nie ma żadnych znaczników, program sam rozpozna bloki
  oddzielone pustą linią: blok, który się powtarza, oznaczy jako `[Chorus]`,
  pozostałe jako kolejne `[Verse]`;
- z metryczki budowane jest pole **Style of Music** — styl, tempo i tonacja
  w jednej linijce;
- na bieżąco liczony jest limit znaków (Suno 5000, Udio 4000). Przekroczenie
  jest sygnalizowane na czerwono.

Opcje **Automatycznie dodaj znaczniki sekcji** i **Dołącz metryczkę** można
wyłączyć, jeśli wolisz sam surowy tekst.

## Pozostałe formaty

- **Czysty tekst** — tytuł, wykonawca i tekst, bez ozdobników.
- **Markdown (z analizą)** — pełny raport: tekst z licznikiem sylab przy każdym
  wersie, metryka, schemat i grupy rymów, powtórzenia, wskaźniki czytelności.
  Dobre do archiwum albo do wysłania komuś do konsultacji.

## Jak to zrobić

**Kopiuj do schowka** — wklejasz prosto do Suno albo Udio.
**Zapisz do pliku** — zapis na dysk.

> Podgląd po prawej pokazuje dokładnie to, co trafi do schowka lub pliku.
""", "en": """
# Export

## Suno and Udio

The program prepares the text in the format AI music generators expect:

- **section markers** are normalised — `[Zwrotka 1]` becomes `[Verse 1]`,
  `[Refren]` → `[Chorus]`, `[Most]` → `[Bridge]`;
- if the text has no markers at all, the program recognises the blocks
  separated by blank lines: a block that repeats is marked `[Chorus]`, the
  rest become successive `[Verse]`;
- the **Style of Music** field is built from the metadata — style, tempo and
  key on one line;
- the character limit is tracked live (Suno 5000, Udio 4000). Going over is
  flagged in red.

**Auto-add section tags** and **Include metadata** can be switched off if you
prefer the raw text.

## Other formats

- **Plain text** — title, artist and lyrics, nothing else.
- **Markdown (with analysis)** — the full report: the lyrics with a syllable
  count beside every line, meter, rhyme scheme and groups, repetitions,
  readability metrics. Good for an archive or for sending to someone for
  feedback.

## How to do it

**Copy to clipboard** — paste straight into Suno or Udio.
**Save to file** — write it to disk.

> The preview on the right shows exactly what goes to the clipboard or file.
"""},

# =========================================================================
"history": {"pl": """
# Historia zmian

Każdy zapis, otwarcie nowego utworu i zamknięcie programu tworzy migawkę
tekstu. Dodatkowo program zapisuje migawkę automatycznie co kilka minut
(domyślnie 5, można zmienić w panelu albo wyłączyć wpisując 0).

Własną migawkę z opisem zapiszesz w polu na górze panelu albo skrótem
**Ctrl+Shift+H**. Warto to robić przed każdą większą przeróbką — opis typu
„przed zmianą refrenu" oszczędza potem sporo szukania.

## Co można zrobić z migawką

- **Podgląd** — kliknięcie na liście pokazuje pełną treść na dole panelu.
- **Różnice** — kolorowe porównanie migawki z tym, co masz teraz. Na zielono
  to, co doszło, na czerwono to, co zniknęło. U góry liczba zmienionych wersów.
- **Przywróć** — wstawia starą wersję do edytora. Zanim to zrobi, zapisuje
  migawkę stanu bieżącego, więc nic nie przepada.
- **Usuń** — kasuje punkt z historii.

## Gdzie to jest trzymane

W bazie SQLite w katalogu danych programu, osobno dla każdego utworu.
Historia przeżywa zamknięcie programu i nie jest częścią pliku `.lyr` —
plik zostaje czysty, do wysłania komukolwiek.

Program pamięta 200 ostatnich migawek każdego utworu.
""", "en": """
# Change history

Every save, every time you open a new song, and closing the program creates a
snapshot of the text. On top of that the program saves one automatically every
few minutes (5 by default; change it in the panel, or set 0 to switch it off).

You can save your own labelled snapshot in the field at the top of the panel
or with **Ctrl+Shift+H**. It is worth doing before every larger rewrite — a
label like "before the chorus rewrite" saves a lot of hunting later.

## What you can do with a snapshot

- **Preview** — clicking it in the list shows the full content below.
- **Differences** — a colour comparison of the snapshot against what you have
  now. Green is what was added, red is what went. The number of changed lines
  is at the top.
- **Restore** — puts the old version back in the editor. Before doing so it
  snapshots the current state, so nothing is lost.
- **Delete** — removes the point from history.

## Where it is kept

In an SQLite database in the program's data folder, separately for each song.
History survives closing the program and is not part of the `.lyr` file — the
file stays clean, ready to send to anyone.

The program keeps the last 200 snapshots per song.
"""},

# =========================================================================
"files": {"pl": """
# Pliki i dane

## Format utworu

Utwory zapisują się jako `.lyr` — to zwykły plik JSON zawierający tekst
i metryczkę. Można go otworzyć dowolnym edytorem tekstu, wersjonować w gicie
i wysłać komuś mailem.

Program otwiera także zwykłe pliki `.txt` i `.md` — wtedy tytuł bierze
z nazwy pliku.

Plik można przekazać w wierszu polecenia albo upuścić na ikonę programu:

    LyricsManagerPro.exe moj-utwor.lyr

## Katalog danych

Wszystko, co program zapamiętuje między uruchomieniami, leży w:

    %APPDATA%\\LyricsManagerPro\\

- `settings.json` — ustawienia i klucz API OpenRoutera,
- `history.db` — historia zmian wszystkich utworów,
- `personal_dictionary.json` — Twoje własne słowa dla sprawdzania pisowni,
- `dictionaries\\` — słowniki Hunspell.

Katalog otworzysz przyciskiem w **Ustawieniach → Ogólne**.

> Kopia zapasowa całego katalogu wystarczy, żeby przenieść program na inny
> komputer razem z historią, słownikami i ustawieniami.

## Diagnostyka

Jeśli coś nie działa, uruchom program z parametrem `--selftest`. Zapisze
raport o zależnościach i widocznych słownikach:

    LyricsManagerPro.exe --selftest raport.txt
""", "en": """
# Files and data

## Song format

Songs are saved as `.lyr` — a plain JSON file holding the lyrics and the
metadata. You can open it in any text editor, keep it in git, and email it to
anyone.

The program also opens ordinary `.txt` and `.md` files — in that case the
title comes from the file name.

A file can be passed on the command line or dropped onto the program icon:

    LyricsManagerPro.exe my-song.lyr

## Data folder

Everything the program remembers between runs lives in:

    %APPDATA%\\LyricsManagerPro\\

- `settings.json` — settings and the OpenRouter API key,
- `history.db` — change history for every song,
- `personal_dictionary.json` — your own words for spell checking,
- `dictionaries\\` — Hunspell dictionaries.

You can open the folder from **Settings → General**.

> A backup of that one folder is enough to move the program to another
> computer together with its history, dictionaries and settings.

## Diagnostics

If something does not work, run the program with `--selftest`. It writes a
report on dependencies and the dictionaries it can see:

    LyricsManagerPro.exe --selftest report.txt
"""},
}
