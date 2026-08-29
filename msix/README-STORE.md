# Pakiet MSIX — Microsoft Store

Wszystko, co potrzebne do wydania Lyrics Manager Pro przez sklep Windows.

---

## Dane rezerwacji

| Pole | Wartość |
|---|---|
| Package/Identity/Name | `MarekZettel-zetmar.LyricsMenagerPro` |
| Package/Identity/Publisher | `CN=15A53D32-C868-48EE-B700-5DBB5449CA1B` |
| Package/Properties/PublisherDisplayName | `Marek Zettel - zetmar` |
| Package Family Name | `MarekZettel-zetmar.LyricsMenagerPro_411qrz2m02jw4` |
| Package SID | `S-1-15-2-2570101063-1518503407-338627846-650014356-1440999148-3067162686-93397780` |
| Identyfikator w Store | `9MVSV3BRHFTV` |
| Adres w sklepie | https://apps.microsoft.com/detail/9MVSV3BRHFTV |

> **Uwaga o nazwie.** W zarezerwowanej nazwie jest literówka: `LyricsMenagerPro`
> zamiast `LyricsManagerPro`. Identity Name musi się zgadzać z rezerwacją co do
> znaku, więc manifest używa jej dokładnie tak. Nazwa widoczna dla użytkowników
> (`DisplayName`) jest poprawna: **Lyrics Manager Pro** — i tylko ona pokazuje
> się w sklepie, w menu Start i na pasku zadań. Literówka siedzi wyłącznie
> w technicznym identyfikatorze, którego nikt nie ogląda.
>
> Jeśli chcesz to naprawić, zarezerwuj w Partner Center nową nazwę
> (`LyricsManagerPro`), ustaw ją jako główną i podmień `Identity/Name`
> w `AppxManifest.xml`. Uwaga: zmiana Identity to z punktu widzenia Windows
> **inna aplikacja** — użytkownicy, którzy zainstalowali starą, nie dostaną
> aktualizacji. Przed pierwszą publikacją zmiana jest bezkosztowa, po
> publikacji już nie.

Poprawność tożsamości jest sprawdzana automatycznie: `tests/test_msix.py` liczy
Package Family Name z manifestu i porównuje z powyższym.

---

## Budowanie

```bash
powershell -ExecutionPolicy Bypass -File msix\build_msix.ps1
```

Skrypt buduje aplikację w wariancie katalogowym, generuje komplet grafik,
składa układ pakietu, tworzy `resources.pri` i pakuje wszystko przez `makeappx`.

Wynik: `dist\LyricsManagerPro-1.0.0.0.msix` (ok. 15,6 MB).

Wymaga Windows SDK (`makeappx.exe`, `makepri.exe`) — skrypt sam znajduje
najnowszą zainstalowaną wersję.

### Wersja

Store wymaga czterech członów, a ostatni musi być zerem:

```bash
powershell -ExecutionPolicy Bypass -File msix\build_msix.ps1 -Version 1.0.1.0
```

Każda kolejna wysyłka musi mieć numer wyższy niż poprzednia.

---

## Wysłanie do Partner Center

**Pakietu nie podpisujesz.** Microsoft podpisuje go sam przy publikacji —
dlatego `Publisher` w manifeście to identyfikator z Twojego konta, a nie
certyfikat, który trzeba by kupić.

1. Partner Center → aplikacja → **Przesyłanie** → **Pakiety**
2. Przeciągnij `dist\LyricsManagerPro-1.0.0.0.msix`
3. Uzupełnij pozostałe sekcje (gotowe treści niżej)
4. Wyślij do certyfikacji

Certyfikacja trwa zwykle od kilku godzin do trzech dni roboczych.

### Czego Microsoft wymaga poza pakietem

| Wymóg | Stan |
|---|---|
| Polityka prywatności (aplikacja łączy się z siecią) | gotowa — [PRIVACY.md](../PRIVACY.md) |
| Kategoria | Produktywność |
| Ocena wiekowa (kwestionariusz IARC) | do wypełnienia w Partner Center |
| Zrzuty ekranu (min. 1, zalecane 4–8, od 1366×768) | do zrobienia |
| Opis sklepu PL i EN | gotowy — niżej |

Adres polityki prywatności do wklejenia w Partner Center:

```
https://github.com/zetmar-collab/lyrics-manager-pro/blob/main/PRIVACY.md
```

---

## Test lokalny przed wysłaniem (opcjonalny)

Niepodpisanego pakietu Windows normalnie nie zainstaluje. Żeby sprawdzić go
u siebie, masz dwie drogi. **Obie zmieniają ustawienia systemu — wykonaj je
świadomie i samodzielnie.**

### Droga A — tryb deweloperski (prościej)

Ustawienia → System → Dla deweloperów → włącz **Tryb dewelopera**, potem:

```
Add-AppxPackage -Path dist\LyricsManagerPro-1.0.0.0.msix -AllowUnsigned
```

### Droga B — własny certyfikat testowy

Wymaga PowerShella uruchomionego jako administrator. Podmiot certyfikatu musi
być identyczny z `Publisher` w manifeście. Pełne polecenia znajdziesz
w dokumentacji Microsoftu „Create a certificate for package signing" —
w skrócie: `New-SelfSignedCertificate` z podmiotem
`CN=15A53D32-C868-48EE-B700-5DBB5449CA1B` i przeznaczeniem do podpisywania kodu,
eksport do `.pfx`, import certyfikatu publicznego do magazynu
`Cert:\LocalMachine\TrustedPeople`, a następnie:

```
powershell -File msix\build_msix.ps1 -Sign -PfxPath test.pfx -PfxPassword haslo
Add-AppxPackage -Path dist\LyricsManagerPro-1.0.0.0.msix
```

Sprzątanie po teście: odinstaluj pakiet przez `Remove-AppxPackage` i usuń
certyfikat testowy z magazynu `TrustedPeople`.

---

## Co warto wiedzieć o wersji ze sklepu

**Dane użytkownika są odseparowane.** Windows przekierowuje zapisy do
`%APPDATA%` na prywatny magazyn pakietu. Wersja ze sklepu i wersja z instalatora
nie widzą więc nawzajem swoich ustawień, historii ani słowników. Kto używa obu,
pobiera słowniki dwa razy. Za to odinstalowanie wersji ze sklepu sprząta po
sobie idealnie.

**Ollama działa.** Aplikacja jest programem Win32 spakowanym w MSIX
(`runFullTrust`), więc działa poza kontenerem AppContainer i pętla zwrotna na
`localhost` nie jest blokowana. W zwykłej aplikacji UWP połączenie z Ollamą
byłoby niemożliwe.

**Aktualizacje idą przez sklep.** Nie trzeba dokładać własnego mechanizmu
aktualizacji.

---

## Gotowe treści do listingu

### Nazwa

```
Lyrics Manager Pro
```

### Krótki opis (PL, do 200 znaków)

```
Warsztat autora tekstów piosenek. Liczy sylaby, wykrywa rymy i powtórzenia, sprawdza pisownię, pomaga AI i eksportuje prosto do Suno oraz Udio.
```

### Opis (PL)

```
Pisanie tekstu piosenki to nie to samo co pisanie tekstu. Wers musi zmieścić się w takt, refren ma wpaść w ucho, a rym nie może być z tych słyszalnych na kilometr. Zwykły edytor nic z tego nie widzi.

Lyrics Manager Pro pokazuje to wszystko w trakcie pisania.

LICZNIK SYLAB
Liczba sylab przy każdym wersie, na bieżąco. Osobne algorytmy dla polskiego i angielskiego. Statystyki, równomierność wersów i podsumowanie każdej sekcji utworu osobno.

ANALIZA RYMÓW
Rymy dokładne, niedokładne i asonanse, rozpoznawane na podstawie uproszczonej transkrypcji fonetycznej. Schemat rymów, gęstość rymowania, rymy wewnętrzne i wyszukiwarka rymów do dowolnego słowa.

POWTÓRZENIA
Powtarzane słowa, frazy i całe wersy, podświetlane wprost w tekście. W refrenie pracują na Ciebie, w zwrotce zwykle znaczą, że tekst stoi w miejscu.

CZYTELNOŚĆ I ŚPIEWALNOŚĆ
Indeks FOG i indeks Pisarka dla polskiego, Flesch i Flesch-Kincaid dla angielskiego, plus wskaźnik śpiewalności i lista wersów zbyt długich, by wygodnie je zaśpiewać.

SPRAWDZANIE PISOWNI
Słowniki Hunspell, te same co w LibreOffice. Dla polskiego wyłapuje przede wszystkim brakujące znaki diakrytyczne, czyli najczęstszy błąd przy szybkim pisaniu. Własny słownik na nazwy własne i celowe zapisy gwarowe.

ASYSTENT AI
Do wyboru Ollama działająca lokalnie na Twoim komputerze albo OpenRouter w chmurze. Jedenaście zadań: alternatywne wersje zwrotki, propozycje rymów, dopisanie dalszego ciągu, dopracowanie języka, śpiewalne tłumaczenie, recenzja tekstu i więcej. Nic nie jest wysyłane bez Twojej decyzji.

EKSPORT DO SUNO I UDIO
Automatyczne rozpoznanie i oznaczenie zwrotek oraz refrenu, pole opisu stylu budowane z metryczki utworu, kontrola limitu znaków. Do tego eksport do czystego tekstu i do Markdown z pełnym raportem analitycznym.

HISTORIA ZMIAN
Migawki tekstu z kolorowanym porównaniem wersji i przywracaniem. Autozapis w tle, żeby nic nie przepadło.

PO POLSKU I PO ANGIELSKU
Trzy niezależne przełączniki: język interfejsu, język analizowanego tekstu i język odpowiedzi AI. Motyw jasny i ciemny. 38 skrótów klawiszowych. Instrukcja obsługi pod klawiszem F1, w obu językach.

Program jest otwartoźródłowy na licencji MIT.
```

### Krótki opis (EN, do 200 znaków)

```
A songwriter's workbench. Counts syllables, finds rhymes and repetitions, checks spelling, brings an AI along and exports straight to Suno and Udio.
```

### Opis (EN)

```
Writing a song lyric is not the same as writing text. A line has to fit the bar, a chorus has to stick, and a rhyme must not be one of those you hear coming a mile away. An ordinary editor sees none of that.

Lyrics Manager Pro shows all of it while you write.

SYLLABLE COUNTER
The syllable count beside every line, live. Separate algorithms for Polish and English. Statistics, line evenness and a summary of every song section separately.

RHYME ANALYSIS
Perfect, slant and assonance rhymes, detected from a simplified phonetic transcription. Rhyme scheme, rhyme density, internal rhymes and a rhyme finder for any word.

REPETITIONS
Repeated words, phrases and whole lines, highlighted right in the text. In a chorus they work for you; in a verse they usually mean the lyrics are going in circles.

READABILITY AND SINGABILITY
FOG and Pisarek indices for Polish, Flesch and Flesch-Kincaid for English, plus a singability measure and a list of lines too long to sing comfortably.

SPELL CHECKING
Hunspell dictionaries, the same ones LibreOffice uses. Your own dictionary for proper nouns and deliberate dialect spellings.

AI ASSISTANT
Choose Ollama running locally on your own computer, or OpenRouter in the cloud. Eleven tasks: alternative versions of a verse, rhyme suggestions, continuing the lyrics, polishing the language, singable translation, a full critique and more. Nothing is sent anywhere without your decision.

EXPORT TO SUNO AND UDIO
Automatic verse and chorus tagging, a style prompt built from the song's metadata, character limit tracking. Plus plain text and Markdown export with a full analysis report.

CHANGE HISTORY
Text snapshots with colour version comparison and restore. Background autosave so nothing is lost.

POLISH AND ENGLISH
Three independent switches: interface language, analysed text language and AI output language. Light and dark theme. 38 keyboard shortcuts. A built-in user guide under F1, in both languages.

The program is open source under the MIT licence.
```

### Słowa kluczowe

```
teksty piosenek, songwriting, sylaby, rymy, pisownia, Suno, Udio, AI, lyrics, syllable counter, rhyme, songwriter, muzyka
```

### Sugerowane zrzuty ekranu

1. Edytor z podświetlonymi rymami — panel Rymy (motyw ciemny)
2. Panel Pisownia z czerwonymi podkreśleniami błędów
3. Panel AI z listą zadań
4. Eksport do Suno z podglądem
5. Instrukcja obsługi (F1)
6. Motyw jasny z panelem Czytelność
