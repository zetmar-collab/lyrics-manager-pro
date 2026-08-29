"""Zrzuty ekranu aplikacji do listingu w Microsoft Store.

Store wymaga plikow PNG o minimalnym rozmiarze 1366x768 dla urzadzen desktop.
Skrypt ustawia okno dokladnie na taki obszar roboczy, wypelnia je przykladowym
utworem i zapisuje ujecia z kolejnych paneli - osobno po polsku i po angielsku.

Uruchomienie:  python tools/make_store_screenshots.py [katalog_docelowy]
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyrics_manager.i18n import set_ui_language, tr
from lyrics_manager.ui.app import LyricsManagerApp

WIDTH, HEIGHT = 1366, 768
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "store-screenshots"

SAMPLE_PL = """[Zwrotka 1]
Wracam do domu nocną drogą
Światła miasta gasną z tyłu
Nie ma juz nic co mnie tu trzyma
Tylko cien na mokrym pyłu

[Refren]
Biegnę przez deszcz, nie licząc kroków
Biegnę przez deszcz, aż zgaśnie noc
Nie zatrzyma mnie nic
Biegnę przez deszcz

[Zwrotka 2]
Pamiętam wszystkie twoje słowa
Choć każde z nich już dawno stygnie
Zostawiam je na dnie kieszeni
I ide dalej, zanim minie
"""

SAMPLE_EN = """[Verse 1]
I walk the road back home tonight
The city lights are fading slow
There's nothing left to hold me here
Just shadowz on the road below

[Chorus]
I'm running through the rain, not counting steps
I'm running through the rain until it clears
And nothing holds me down
I'm running through the rain

[Verse 2]
I still remember every word
Though every one of them turns colder
I keep them at the pocket's bottom
And walk away before it's over
"""

USER32 = ctypes.windll.user32


def client_box(hwnd: int) -> tuple[int, int, int, int]:
    """Prostokat obszaru roboczego okna w koordynatach ekranu."""
    rect = wintypes.RECT()
    USER32.GetClientRect(hwnd, ctypes.byref(rect))
    point = wintypes.POINT(rect.left, rect.top)
    USER32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + rect.right, point.y + rect.bottom


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)

    app = LyricsManagerApp()
    app.geometry(f"{WIDTH}x{HEIGHT}+60+40")
    app.attributes("-topmost", True)
    app.update()
    app.lift()
    app.focus_force()

    hwnd = int(app.winfo_id())
    # winfo_id() zwraca uchwyt obszaru rysowania; okno najwyzszego poziomu to
    # jego rodzic - dopiero ono ma pelny obszar roboczy
    top = USER32.GetAncestor(hwnd, 2)   # GA_ROOT

    def settle(seconds: float = 1.2) -> None:
        end = time.time() + seconds
        while time.time() < end:
            app.update()
            time.sleep(0.05)

    def grab_once():
        """Jedno ujecie obszaru roboczego okna."""
        app.attributes("-topmost", True)
        app.deiconify()
        app.lift()
        app.focus_force()
        settle(1.4)
        left, top_y, right, bottom = client_box(top)
        image = ImageGrab.grab(bbox=(left, top_y, right, bottom))
        if image.size != (WIDTH, HEIGHT):
            image = image.resize((WIDTH, HEIGHT))
        return image

    def looks_blank(image) -> bool:
        """Czy zrzut jest jednolita plama.

        Gdy okno przestanie sie rysowac (utrata pierwszego planu, wygaszacz),
        ImageGrab zwraca czarny prostokat. Taki plik trafilby do sklepu jako
        pusty ekran, wiec sprawdzamy rozpietosc kolorow.
        """
        extremes = image.convert("RGB").getextrema()
        spread = max(high - low for low, high in extremes)
        return spread < 40

    def shot(name: str) -> None:
        for attempt in range(1, 4):
            image = grab_once()
            if not looks_blank(image):
                image.save(out / name)
                print(f"  {name}  {image.size[0]}x{image.size[1]}")
                return
            print(f"  {name}  pusty zrzut, ponawiam ({attempt}/3)")
            settle(2.0)
        raise RuntimeError(f"Nie udalo sie zrobic czytelnego zrzutu: {name}")

    def wait_for_spelling() -> None:
        deadline = time.time() + 45
        while time.time() < deadline:
            app.update()
            if app._spell_state in ("ready", "missing", "no_engine"):
                return
            time.sleep(0.2)

    def capture_set(lang: str, sample: str, prefix: str) -> None:
        print(f"{prefix}:")
        app._on_ui_lang(lang.upper())
        app.set_text_language(lang)
        app.set_text(sample)
        app.meta_title.delete(0, "end")
        app.meta_title.insert(0, "Biegnę przez deszcz" if lang == "pl" else "Running Through The Rain")
        app.meta_artist.delete(0, "end")
        app.meta_style.delete(0, "end")
        app.meta_style.insert(0, "indie folk, acoustic guitar, female vocal")
        app.meta_tempo.delete(0, "end")
        app.meta_tempo.insert(0, "96")
        app._on_meta_change()

        # Slownik musi pasowac do jezyka zrzutu, inaczej na ekranie widac
        # setki falszywych bledow pisowni.
        from lyrics_manager.spelling import installed_codes
        wanted = "pl_PL" if lang == "pl" else "en_US"
        if wanted in installed_codes():
            app.set_spell_dictionary(wanted)

        app._run_analysis()
        app.request_spellcheck(force=True)
        wait_for_spelling()
        settle(1.5)

        app._on_theme(tr("theme.dark"))
        app.tabs.select("rhymes");      shot(f"{prefix}-1-rymy.png")
        app.tabs.select("spelling");    shot(f"{prefix}-2-pisownia.png")
        app.tabs.select("ai");          shot(f"{prefix}-3-ai.png")

        app._on_theme(tr("theme.light"))
        settle(0.8)
        app.tabs.select("export");      shot(f"{prefix}-4-eksport.png")
        app.tabs.select("readability"); shot(f"{prefix}-5-czytelnosc.png")

        app._on_theme(tr("theme.dark"))
        settle(0.5)

    capture_set("pl", SAMPLE_PL, "pl")
    capture_set("en", SAMPLE_EN, "en")

    # sprzatanie po sesji zrzutow - nie zostawiamy smieci w historii
    app._dirty = False
    try:
        for snapshot in app.history.list(app.song_key()):
            app.history.delete(snapshot.id)
    except Exception:
        pass
    app.destroy()

    files = sorted(out.glob("*.png"))
    print(f"\nZapisano {len(files)} zrzutow w {out}")


if __name__ == "__main__":
    main()
