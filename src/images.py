import io
import os
import time
import urllib.parse

import requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350  # 4:5 portrait, best use of feed space
WATERMARK_PAD = 100
ACCENT = (0, 200, 255)

BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
REG_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def _wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _gradient(top, bottom):
    img = Image.new("RGB", (W, H))
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def _ai_background(prompt):
    """Free image generation via Pollinations. Falls back to a gradient on failure."""
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt + ", cinematic, dramatic lighting, high detail, no text")
        + f"?width={W}&height={H + WATERMARK_PAD}&nologo=true&model=flux"
    )
    for attempt in range(4):
        if attempt:
            time.sleep(50)  # free tier: 1 image per 45s per IP
        try:
            r = requests.get(url, timeout=120)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                # Drop the bottom strip where the provider stamps its watermark
                img = img.crop((0, 0, img.width, int(img.height * H / (H + WATERMARK_PAD))))
                scale = max(W / img.width, H / img.height)
                img = img.resize((int(img.width * scale), int(img.height * scale)))
                left, top = (img.width - W) // 2, (img.height - H) // 2
                return img.crop((left, top, left + W, top + H))
        except requests.RequestException:
            pass
    return _gradient((10, 20, 60), (80, 20, 120))


def _darken_bottom(img, start=0.35):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(int(H * start), H):
        alpha = int(235 * (y - H * start) / (H * (1 - start)))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _footer(d, handle, text):
    d.text((70, H - 90), handle, font=_font(BOLD_FONTS, 34), fill=(255, 255, 255))
    f = _font(REG_FONTS, 34)
    d.text((W - 70 - d.textlength(text, font=f), H - 90), text, font=f, fill=ACCENT)


def cover(headline, image_prompt, handle):
    img = _darken_bottom(_ai_background(image_prompt))
    d = ImageDraw.Draw(img)
    tag_f = _font(BOLD_FONTS, 34)
    d.rounded_rectangle((70, 70, 70 + d.textlength("TECH NEWS", font=tag_f) + 50, 140), 35, fill=ACCENT)
    d.text((95, 85), "TECH NEWS", font=tag_f, fill=(0, 0, 0))

    f = _font(BOLD_FONTS, 92)
    lines = _wrap(d, headline.upper(), f, W - 140)
    while len(lines) > 5:
        f = _font(BOLD_FONTS, f.size - 8)
        lines = _wrap(d, headline.upper(), f, W - 140)
    y = H - 160 - len(lines) * (f.size + 14)
    for line in lines:
        d.text((70, y), line, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
        y += f.size + 14
    _footer(d, handle, "Swipe  >")
    return img


def takeaways(points, handle):
    img = _gradient((12, 18, 45), (45, 15, 80))
    d = ImageDraw.Draw(img)
    d.text((70, 90), "KEY TAKEAWAYS", font=_font(BOLD_FONTS, 54), fill=ACCENT)
    f = _font(REG_FONTS, 50)
    wrapped = [_wrap(d, p, f, W - 70 - 190 - 40) for p in points[:3]]
    block = sum(len(w) * 66 + 90 for w in wrapped) - 90
    y = 150 + (H - 150 - 150 - block) // 2  # center between title and footer
    for i, p in enumerate(points[:3], 1):
        d.ellipse((70, y, 150, y + 80), fill=ACCENT)
        d.text((110, y + 40), str(i), font=_font(BOLD_FONTS, 46), fill=(0, 0, 0), anchor="mm")
        for line in wrapped[i - 1]:
            d.text((190, y + 4), line, font=f, fill=(255, 255, 255))
            y += 66
        y += 90
    _footer(d, handle, "Swipe  >")
    return img


def outro(handle):
    img = _gradient((45, 15, 80), (0, 90, 140))
    d = ImageDraw.Draw(img)
    big = _font(BOLD_FONTS, 96)
    y = 400
    for line in ["Want daily", "tech news?"]:
        d.text((W / 2, y), line, font=big, fill=(255, 255, 255), anchor="mm")
        y += 120
    d.text((W / 2, y + 40), f"Follow {handle}", font=_font(BOLD_FONTS, 62), fill=ACCENT, anchor="mm")
    sub = _font(REG_FONTS, 44)
    d.text((W / 2, y + 160), "Save this post  |  Share with a friend", font=sub, fill=(255, 255, 255), anchor="mm")
    return img


def build_slides(data, handle, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    slides = [
        cover(data["headline"], data["image_prompt"], handle),
        takeaways(data["points"], handle),
        outro(handle),
    ]
    paths = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(out_dir, f"slide{i}.jpg")
        s.save(p, quality=92)
        paths.append(p)
    return paths
