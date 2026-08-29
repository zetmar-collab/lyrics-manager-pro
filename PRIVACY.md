# Polityka prywatności / Privacy Policy

**Lyrics Manager Pro** · wersja 1.0.0 · ostatnia aktualizacja: 1 sierpnia 2026

---

## Wersja polska

### Krótko

Program nie zbiera o Tobie żadnych danych. Nie ma kont, logowania, telemetrii
ani analityki. Twoje teksty są Twoje i zostają na Twoim komputerze, chyba że
sam poprosisz o pomoc AI w chmurze.

### Co jest przechowywane i gdzie

Wszystko zapisuje się wyłącznie lokalnie, w katalogu danych aplikacji
(`%APPDATA%\LyricsManagerPro`, a w wersji ze sklepu Microsoft w prywatnym
magazynie pakietu):

| Dane | Do czego służą |
|---|---|
| Ustawienia programu | zapamiętanie języka, motywu, rozmiaru czcionki |
| Klucz API OpenRouter | żebyś nie wpisywał go przy każdym uruchomieniu |
| Historia zmian tekstów | podgląd i przywracanie wcześniejszych wersji |
| Twój słownik pisowni | słowa, które sam oznaczyłeś jako poprawne |
| Słowniki Hunspell | sprawdzanie pisowni bez połączenia z siecią |

Pliki z utworami zapisujesz tam, gdzie sam wskażesz. Program nigdzie ich nie
kopiuje ani nie wysyła.

### Kiedy program łączy się z internetem

Nigdy sam z siebie. Połączenie następuje tylko wtedy, gdy klikniesz konkretną
rzecz:

**1. Pobranie słownika pisowni** — pobiera plik z publicznego repozytorium
GitHub (`raw.githubusercontent.com`). Wysyłane jest wyłącznie zwykłe żądanie
pobrania pliku. Nie przekazujemy przy tym żadnych Twoich danych ani tekstów.

**2. Asystent AI — Ollama (lokalnie)** — połączenie idzie na Twój własny
komputer (domyślnie `http://localhost:11434`) albo pod adres, który sam
wskażesz. Tekst nie opuszcza Twojej sieci.

**3. Asystent AI — OpenRouter (chmura)** — dopiero to wysyła dane poza Twój
komputer. Gdy uruchomisz zadanie AI z wybranym silnikiem OpenRouter, do
serwera `openrouter.ai` trafia: fragment tekstu, na którym pracujesz, kontekst
utworu (tytuł, wykonawca, styl, wykryty schemat rymów, liczba sylab w wersach),
Twoje dodatkowe wskazówki oraz Twój klucz API. Podlega to wtedy polityce
prywatności OpenRouter: <https://openrouter.ai/privacy>.

To Ty decydujesz, którego silnika użyć. Jeśli nie chcesz wysyłać niczego poza
komputer, korzystaj z Ollamy albo w ogóle nie używaj panelu AI — reszta
programu działa bez połączenia z siecią.

### Czego program nie robi

- nie zbiera telemetrii ani statystyk użycia,
- nie wysyła raportów o błędach,
- nie wyświetla reklam,
- nie zakłada konta i nie wymaga logowania,
- nie udostępnia niczego osobom trzecim,
- nie śledzi Cię między urządzeniami.

### Dzieci

Program nie jest kierowany do dzieci poniżej 13 roku życia i nie zbiera od nich
żadnych danych, ponieważ nie zbiera ich od nikogo.

### Usunięcie danych

Odinstaluj program albo skasuj katalog `%APPDATA%\LyricsManagerPro`.
W wersji ze sklepu Microsoft odinstalowanie usuwa wszystkie dane automatycznie.
Katalog danych otworzysz w programie: **Ustawienia → Ogólne → Otwórz katalog**.

### Kod źródłowy

Program jest otwarty. Każdy może sprawdzić, co robi:
<https://github.com/zetmar-collab/lyrics-manager-pro>

### Kontakt

Marek Zettel · <https://github.com/zetmar-collab/lyrics-manager-pro/issues>

---

## English version

### In short

The program collects no data about you. There are no accounts, no logins, no
telemetry, no analytics. Your lyrics are yours and they stay on your computer,
unless you explicitly ask a cloud AI for help.

### What is stored and where

Everything is stored locally only, in the application data folder
(`%APPDATA%\LyricsManagerPro`, or the package's private store in the Microsoft
Store version):

| Data | Purpose |
|---|---|
| Program settings | remembering language, theme, font size |
| OpenRouter API key | so you do not retype it on every launch |
| Lyrics change history | previewing and restoring earlier versions |
| Your personal dictionary | words you marked as correct yourself |
| Hunspell dictionaries | offline spell checking |

Song files are saved wherever you choose. The program never copies or uploads
them.

### When the program connects to the internet

Never on its own. A connection happens only when you click something specific:

**1. Downloading a spelling dictionary** — fetches a file from a public GitHub
repository (`raw.githubusercontent.com`). Only a plain file request is sent. No
data or text of yours is included.

**2. AI assistant — Ollama (local)** — the connection goes to your own computer
(`http://localhost:11434` by default) or to an address you configure yourself.
Your text never leaves your network.

**3. AI assistant — OpenRouter (cloud)** — this is the only feature that sends
data off your computer. When you run an AI task with the OpenRouter engine
selected, the following is sent to `openrouter.ai`: the passage you are working
on, the song's context (title, artist, style, detected rhyme scheme, syllable
counts per line), your extra instructions, and your API key. OpenRouter's
privacy policy then applies: <https://openrouter.ai/privacy>.

You choose which engine to use. If you do not want anything leaving your
computer, use Ollama or simply do not use the AI panel — the rest of the
program works entirely offline.

### What the program does not do

- no telemetry or usage statistics,
- no crash reporting,
- no advertising,
- no account, no sign-in,
- no sharing with third parties,
- no cross-device tracking.

### Children

The program is not directed at children under 13 and collects no data from
them, because it collects no data from anyone.

### Deleting your data

Uninstall the program or delete the `%APPDATA%\LyricsManagerPro` folder. In the
Microsoft Store version, uninstalling removes all data automatically. You can
open the data folder from **Settings → General → Open folder**.

### Source code

The program is open source. Anyone can check what it does:
<https://github.com/zetmar-collab/lyrics-manager-pro>

### Contact

Marek Zettel · <https://github.com/zetmar-collab/lyrics-manager-pro/issues>
