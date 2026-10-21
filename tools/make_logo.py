"""Generate the TECHBOLT logo files into assets/.

    python tools/make_logo.py

Outputs: logo.png (for dark slides), logo_ink.png (for the accent-coloured slide). The profile picture is made by tools/make_profile_3d.py.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets")
NAME = os.environ.get("BRAND_NAME", "TECHBOLT").upper()
ACCENT = tuple(int(os.environ.get("BRAND_ACCENT", "2E90FF")[i:i + 2], 16) for i in (0, 2, 4))
INK = (10, 10, 14)
HILITE = tuple(int(c + (255 - c) * 0.38) for c in ACCENT)  # lighter blue, readable on bright backgrounds
WHITE = (245, 245, 247)
SS = 4  # supersampling for smooth edges

# A "T" whose stem is a lightning bolt, in unit coordinates
T_BOLT = [
    (0.16, 0.15), (0.84, 0.15), (0.84, 0.33), (0.62, 0.33), (0.50, 0.55), (0.68, 0.55),
    (0.36, 0.90), (0.45, 0.62), (0.28, 0.62), (0.38, 0.33), (0.16, 0.33),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(ASSETS, "fonts", name), size)


def mark(size, tile, glyph, radius=0.26):
    """Rounded square tile with the T-bolt cut out of it."""
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, s - 1, s - 1), int(s * radius), fill=tile)
    d.polygon([(x * s, y * s) for x, y in T_BOLT], fill=glyph)
    return img.resize((size, size), Image.LANCZOS)


def lockup(tile, glyph, word_a, word_b, height=256):
    f = font("Barlow-ExtraBold.ttf", int(height * 0.60))
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    wa, wb = probe.textlength(NAME[:4], font=f), probe.textlength(NAME[4:], font=f)
    gap = int(height * 0.28)
    img = Image.new("RGBA", (int(height + gap + wa + wb + 8), height), (0, 0, 0, 0))
    img.paste(mark(height, tile, glyph), (0, 0))
    d = ImageDraw.Draw(img)
    x, cy = height + gap, height / 2
    d.text((x, cy), NAME[:4], font=f, fill=word_a, anchor="lm")
    d.text((x + wa, cy), NAME[4:], font=f, fill=word_b, anchor="lm")
    return img


if __name__ == "__main__":
    lockup(ACCENT, INK, WHITE, HILITE).save(os.path.join(ASSETS, "logo.png"))
    lockup(INK, ACCENT, INK, INK).save(os.path.join(ASSETS, "logo_ink.png"))
    print("Wrote logo.png, logo_ink.png to", os.path.normpath(ASSETS))
