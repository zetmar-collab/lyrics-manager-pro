"""Testy pakietu MSIX dla Microsoft Store.

Najwazniejszy z nich liczy Package Family Name z manifestu i porownuje go
z tym zarezerwowanym w Partner Center. Gdyby ktos kiedys poprawil literowke
w Identity Name albo zmienil Publisher, Windows uznalby to za inna aplikacje
i uzytkownicy nie dostaliby aktualizacji - ten test to wychwyci.

Uruchomienie: python tests\\test_msix.py
"""

from __future__ import annotations

import hashlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "msix" / "AppxManifest.xml"
ASSETS = ROOT / "msix" / "Assets"

# Dane z rezerwacji w Partner Center (Zarzadzanie produktem -> Tozsamosc
# produktu). Nie zmieniaj tego bez zmiany rezerwacji - Partner Center odrzuca
# pakiet, ktorego Identity nie zgadza sie z zarezerwowana nazwa.
EXPECTED_NAME = "MarekZettel-zetmar.LyricsManagerPro"
EXPECTED_PUBLISHER = "CN=15A53D32-C868-48EE-B700-5DBB5449CA1B"
EXPECTED_PUBLISHER_DISPLAY = "Marek Zettel - zetmar"
EXPECTED_PFN = "MarekZettel-zetmar.LyricsManagerPro_411qrz2m02jw4"

NS = {
    "": "http://schemas.microsoft.com/appx/manifest/foundation/windows10",
    "uap": "http://schemas.microsoft.com/appx/manifest/uap/windows10",
    "rescap": "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities",
}

FAILURES: list[str] = []
SKIPPED: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual != expected:
        FAILURES.append(f"{label}: oczekiwano {expected!r}, jest {actual!r}")


def check_true(label: str, condition: bool) -> None:
    if not condition:
        FAILURES.append(f"{label}: warunek nie zostal spelniony")


# --- Package Family Name --------------------------------------------------

# base32 wedlug Crockforda, bez liter i, l, o, u
PFN_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"


def publisher_hash(publisher: str) -> str:
    """Skrot wydawcy uzywany w PFN: 8 pierwszych bajtow SHA-256 z UTF-16LE."""
    digest = hashlib.sha256(publisher.encode("utf-16-le")).digest()[:8]
    bits = "".join(f"{byte:08b}" for byte in digest) + "0" * 5
    return "".join(PFN_ALPHABET[int(bits[i:i + 5], 2)] for i in range(0, 65, 5))


# kontrola samej funkcji na znanej parze z dokumentacji Microsoftu
check("skrot wydawcy - przypadek kontrolny",
      publisher_hash("CN=Microsoft Corporation, O=Microsoft Corporation, "
                     "L=Redmond, S=Washington, C=US"),
      "8wekyb3d8bbwe")

# --- manifest -------------------------------------------------------------

check_true("manifest istnieje", MANIFEST.exists())

if MANIFEST.exists():
    tree = ET.parse(MANIFEST)
    root = tree.getroot()

    identity = root.find("Identity", NS)
    check_true("manifest ma sekcje Identity", identity is not None)

    if identity is not None:
        name = identity.get("Name")
        publisher = identity.get("Publisher")
        version = identity.get("Version")
        architecture = identity.get("ProcessorArchitecture")

        check("Identity/Name", name, EXPECTED_NAME)
        check("Identity/Publisher", publisher, EXPECTED_PUBLISHER)
        check("Package Family Name", f"{name}_{publisher_hash(publisher)}", EXPECTED_PFN)
        check("architektura", architecture, "x64")

        # Store wymaga czterech czlonow, ostatni musi byc zerem
        check_true(f"wersja {version} ma cztery czlony",
                   bool(re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version or "")))
        check_true(f"wersja {version} konczy sie zerem",
                   bool(version) and version.split(".")[-1] == "0")

    props = root.find("Properties", NS)
    check_true("manifest ma sekcje Properties", props is not None)
    if props is not None:
        display = props.find("DisplayName", NS)
        pub_display = props.find("PublisherDisplayName", NS)
        check("PublisherDisplayName", pub_display.text if pub_display is not None else None,
              EXPECTED_PUBLISHER_DISPLAY)
        # nazwa dla uzytkownika ma byc poprawna, mimo literowki w Identity
        check("DisplayName", display.text if display is not None else None,
              "Lyrics Manager Pro")

    # aplikacja pelnego zaufania - inaczej nie zadziala polaczenie z Ollama
    app = root.find("Applications/Application", NS)
    check_true("manifest ma sekcje Application", app is not None)
    if app is not None:
        check("EntryPoint", app.get("EntryPoint"), "Windows.FullTrustApplication")
        check("Executable", app.get("Executable"), "LyricsManagerPro.exe")

    capabilities = root.find("Capabilities", NS)
    check_true("manifest ma sekcje Capabilities", capabilities is not None)
    if capabilities is not None:
        declared = {
            element.get("Name")
            for element in capabilities
        }
        check_true("zadeklarowano runFullTrust", "runFullTrust" in declared)
        check_true("zadeklarowano internetClient", "internetClient" in declared)

    # kazda grafika wymieniona w manifescie musi istniec
    referenced: set[str] = set()
    for element in root.iter():
        for value in element.attrib.values():
            if value.lower().endswith(".png"):
                referenced.add(value.replace("\\", "/"))
        if element.tag.endswith("}Logo") and element.text:
            referenced.add(element.text.replace("\\", "/"))

    check_true("manifest wskazuje jakies grafiki", len(referenced) >= 6)
    for relative in sorted(referenced):
        path = ROOT / "msix" / relative
        check_true(f"grafika istnieje: {relative}", path.exists())

# --- komplet grafik -------------------------------------------------------

if ASSETS.exists():
    required = [
        "StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png",
        "Square310x310Logo.png", "Wide310x150Logo.png", "Square71x71Logo.png",
        "SplashScreen.png",
    ]
    for name in required:
        check_true(f"grafika {name}", (ASSETS / name).exists())

    # warianty dla paska zadan
    for size in (16, 24, 32, 48, 256):
        check_true(f"wariant targetsize-{size}",
                   (ASSETS / f"Square44x44Logo.targetsize-{size}.png").exists())
        check_true(f"wariant targetsize-{size} unplated",
                   (ASSETS / f"Square44x44Logo.targetsize-{size}_altform-unplated.png").exists())
else:
    SKIPPED.append("brak katalogu msix/Assets - uruchom tools/make_store_assets.py")

# --- zbudowany pakiet -----------------------------------------------------

packages = sorted((ROOT / "dist").glob("LyricsManagerPro-*.msix")) if (ROOT / "dist").exists() else []
if packages:
    package = packages[-1]
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        check_true("pakiet zawiera manifest", "AppxManifest.xml" in names)
        check_true("pakiet zawiera program", "LyricsManagerPro.exe" in names)
        check_true("pakiet zawiera resources.pri", "resources.pri" in names)
        check_true("pakiet zawiera grafiki",
                   sum(1 for n in names if n.startswith("Assets/")) >= 20)
        check_true("pakiet zawiera biblioteki Pythona",
                   any(n.startswith("_internal/") for n in names))

        packed = archive.read("AppxManifest.xml").decode("utf-8")
        packed_name = re.search(r'Name="([^"]+)"', packed)
        packed_publisher = re.search(r'Publisher="([^"]+)"', packed)
        check("Name w spakowanym manifescie",
              packed_name.group(1) if packed_name else None, EXPECTED_NAME)
        check("Publisher w spakowanym manifescie",
              packed_publisher.group(1) if packed_publisher else None, EXPECTED_PUBLISHER)
else:
    SKIPPED.append("brak zbudowanego pakietu .msix - uruchom msix/build_msix.ps1")

# --- wynik ----------------------------------------------------------------

for note in SKIPPED:
    print("POMINIETO:", note)

if FAILURES:
    print(f"NIEPOWODZENIA ({len(FAILURES)}):")
    for failure in FAILURES:
        print("  -", failure)
    raise SystemExit(1)

print("Wszystkie testy pakietu MSIX przeszly.")
