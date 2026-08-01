"""Generuje ikone aplikacji assets/app.ico (nuta na gradiencie + linie tekstu)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "app.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]

BG_TOP = (37, 99, 235)      # niebieski
BG_BOTTOM = (124, 58, 237)  # fiolet
INK = (255, 255, 255)


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # tlo: zaokraglony kwadrat z pionowym gradientem
    radius = max(2, size // 5)
    gradient = Image.new("RGBA", (1, size))
    for y in range(size):
        t = y / max(1, size - 1)
        gradient.putpixel((0, y), (
            int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t),
            int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t),
            int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t),
            255,
        ))
    gradient = gradient.resize((size, size))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius, fill=255)
    img.paste(gradient, (0, 0), mask)

    unit = size / 32.0

    # linie tekstu po lewej
    line_x0 = 6 * unit
    for i, width in enumerate((11, 8, 11, 6)):
        y = (9 + i * 4.2) * unit
        draw.rounded_rectangle(
            [line_x0, y, line_x0 + width * unit, y + 1.6 * unit],
            radius=max(1, int(0.8 * unit)), fill=INK + (215,),
        )

    # nuta po prawej
    stem_x = 24 * unit
    draw.rounded_rectangle(
        [stem_x, 7 * unit, stem_x + 1.7 * unit, 21 * unit],
        radius=max(1, int(0.8 * unit)), fill=INK,
    )
    head_r = 3.2 * unit
    draw.ellipse(
        [stem_x - head_r * 1.55, 19 * unit, stem_x + head_r * 0.55, 19 * unit + head_r * 1.7],
        fill=INK,
    )
    # choragiewka
    draw.polygon(
        [(stem_x + 1.7 * unit, 7 * unit),
         (stem_x + 6.5 * unit, 10 * unit),
         (stem_x + 6.5 * unit, 13.5 * unit),
         (stem_x + 1.7 * unit, 10.5 * unit)],
        fill=INK,
    )
    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Zapisujemy z najwiekszego obrazu - PIL sam wygeneruje mniejsze warianty.
    # (Zapis z malego obrazu daje ikone tylko w jednym rozmiarze.)
    base = draw_icon(256)
    base.save(OUT, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"Zapisano {OUT}")


if __name__ == "__main__":
    main()
