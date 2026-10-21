"""Generate the 3D Instagram/Facebook profile picture into assets/profile.png.

    python tools/make_profile_3d.py

An extruded blue T-bolt with a lit edge and soft shadow on the dark brand background.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_logo as ml
from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 1080
ACC, INK = ml.ACCENT, ml.INK


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def background():
    img = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        d.line([(0, y), (S, y)], fill=lerp((10, 26, 66), (5, 6, 14), y / S))
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for k in range(0, S, 60):
        ld.line([(k, 0), (k, S)], fill=ACC + (22,), width=2)
        ld.line([(0, k), (S, k)], fill=ACC + (22,), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), layer)
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((S / 2 - 360, S / 2 - 330, S / 2 + 360, S / 2 + 390), fill=ACC + (120,))
    return Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(190)))


def make(depth=(62, 82), scale=0.64, tilt=-7):
    steps = 90
    dx, dy = depth[0] / steps, depth[1] / steps
    cx, cy = S / 2 - depth[0] / 2, S / 2 - depth[1] / 2
    pts = [(cx + (x - 0.5) * S * scale, cy + (y - 0.5) * S * scale) for x, y in ml.T_BOLT]

    img = background()

    # soft drop shadow on the "floor"
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + depth[0] + 36, y + depth[1] + 54) for x, y in pts], fill=(0, 0, 0, 190))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(34)))

    obj = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(obj)
    # extrusion: back to front, darker the further back
    for i in range(steps, 0, -1):
        c = lerp((16, 58, 150), (3, 14, 52), i / steps)
        od.polygon([(x + dx * i, y + dy * i) for x, y in pts], fill=c + (255,))

    # front face with a diagonal gradient
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for k in range(-S, 2 * S):
        t = max(0, min(1, (k + S * 0.2) / (S * 1.15)))
        gd.line([(k, 0), (k - S, S)], fill=lerp((160, 220, 255), (44, 144, 255), t), width=2)
    obj.paste(grad, (0, 0), mask)

    # bevel: a bright rim along the top-left edges only
    lit = ImageChops.subtract(mask, ImageChops.offset(mask, 8, 8))
    white = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    obj.paste(white, (0, 0), lit.point(lambda v: int(v * 0.85)))

    obj = obj.rotate(tilt, resample=Image.BICUBIC, center=(S / 2, S / 2))
    img = Image.alpha_composite(img, obj)
    return img.convert("RGB")


if __name__ == "__main__":
    out = os.path.join(ml.ASSETS, "profile.png")
    make().save(out)
    print("Wrote", os.path.normpath(out))
