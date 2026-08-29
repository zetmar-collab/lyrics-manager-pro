"""Generuje komplet grafik wymaganych przez pakiet MSIX / Microsoft Store.

Rysunek jest ten sam co w ikonie aplikacji (tools/make_icon.py) - kafelki
dostaja go na przezroczystym tle z marginesem, zeby Windows mogl podlozyc
wlasny kolor kafelka.

Uruchomienie:  python tools/make_store_assets.py [katalog_docelowy]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_icon import draw_icon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "msix" / "Assets"

# (nazwa pliku, bok w px, udzial rysunku w kafelku)
# Windows zaleca, zeby logo zajmowalo ok. 2/3 kafelka - reszta to oddech.
ASSETS: list[tuple[str, int, int, float]] = [
    # nazwa,                          szerokosc, wysokosc, wypelnienie
    ("StoreLogo.png",                    50,  50, 1.00),
    ("StoreLogo.scale-200.png",         100, 100, 1.00),
    ("Square44x44Logo.png",              44,  44, 1.00),
    ("Square44x44Logo.scale-200.png",    88,  88, 1.00),
    ("Square71x71Logo.png",              71,  71, 0.66),
    ("Square71x71Logo.scale-200.png",   142, 142, 0.66),
    ("Square150x150Logo.png",           150, 150, 0.66),
    ("Square150x150Logo.scale-200.png", 300, 300, 0.66),
    ("Square310x310Logo.png",           310, 310, 0.66),
    ("Square310x310Logo.scale-200.png", 620, 620, 0.66),
    ("Wide310x150Logo.png",             310, 150, 0.66),
    ("Wide310x150Logo.scale-200.png",   620, 300, 0.66),
    ("SplashScreen.png",                620, 300, 0.50),
    ("SplashScreen.scale-200.png",     1240, 600, 0.50),
]

# Warianty ikony listy aplikacji - Windows uzywa ich na pasku zadan i w menu.
TARGET_SIZES = [16, 24, 32, 48, 256]


def compose(width: int, height: int, fill: float) -> Image.Image:
    """Rysunek wpisany w plotno o zadanych wymiarach, na przezroczystym tle."""
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    art_size = max(16, int(min(width, height) * fill))
    art = draw_icon(art_size)
    canvas.paste(art, ((width - art_size) // 2, (height - art_size) // 2), art)
    return canvas


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)

    for name, width, height, fill in ASSETS:
        compose(width, height, fill).save(out / name)

    # Square44x44Logo.targetsize-*.png - ikona bez marginesu, dla paska zadan.
    # Wariant altform-unplated Windows pokazuje bez tla, wiec musi byc ten sam
    # rysunek, tyle ze bez podkladu systemowego.
    for size in TARGET_SIZES:
        art = draw_icon(size) if size >= 48 else draw_icon(256).resize(
            (size, size), Image.LANCZOS)
        art.save(out / f"Square44x44Logo.targetsize-{size}.png")
        art.save(out / f"Square44x44Logo.targetsize-{size}_altform-unplated.png")

    produced = sorted(p.name for p in out.glob("*.png"))
    print(f"Zapisano {len(produced)} plikow w {out}")
    for name in produced:
        size = (out / name).stat().st_size
        print(f"  {name:<52} {size:>7} B")


if __name__ == "__main__":
    main()
