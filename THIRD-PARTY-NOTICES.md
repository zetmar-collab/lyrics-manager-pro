# Składniki innych autorów / Third-party components

Lyrics Manager Pro jest wydany na licencji [MIT](LICENSE). Do gotowego pliku
`.exe` dołączone są poniższe biblioteki open source, każda na własnej licencji.

*Lyrics Manager Pro is released under the [MIT](LICENSE) licence. The following
open-source libraries are bundled into the built `.exe`, each under its own
licence.*

| Składnik / Component | Licencja / Licence | Adres / Home |
|---|---|---|
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | MIT | interfejs graficzny |
| [requests](https://github.com/psf/requests) | Apache License 2.0 | komunikacja HTTP |
| [spylls](https://github.com/zverok/spylls) | MIT | silnik pisowni Hunspell w Pythonie |
| [Python](https://www.python.org) | PSF License | środowisko uruchomieniowe |

## Słowniki pisowni / Spelling dictionaries

Słowniki **nie są** częścią programu ani instalatora. Program pobiera je na
żądanie z oficjalnego repozytorium
[LibreOffice/dictionaries](https://github.com/LibreOffice/dictionaries)
i pozostają one na swoich licencjach:

- **pl_PL** — LGPL / MPL / CC-BY-SA, źródło: [sjp.pl](https://sjp.pl/slownik/ort/)
- **en_US, en_GB** — LGPL / BSD, źródło: [SCOWL](http://wordlist.aspell.net/)

Pobierając słownik w programie, akceptujesz licencję jego autorów. Program
pokazuje licencję przy każdym słowniku w oknie **Słowniki…**.

*Dictionaries are **not** part of the program or the installer. They are
downloaded on demand from the official LibreOffice dictionary repository and
remain under their own licences. The Dictionaries window shows the licence next
to each dictionary.*
