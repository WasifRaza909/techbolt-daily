"""Fetch the readable text of a news article so the AI writes from facts, not just a headline."""
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

UA = "Mozilla/5.0 (compatible; TechBoltBot/1.0; +https://github.com/WasifRaza909/techbolt-daily)"
SKIP = {"script", "style", "noscript", "nav", "footer", "header", "aside", "form", "figcaption", "svg", "button"}
MAX_CHARS = 6000


class _Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_p = False
        self.buf = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif tag == "p" and not self.skip:
            self.in_p, self.buf = True, []

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        elif tag == "p" and self.in_p:
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if len(text) >= 60:
                self.paragraphs.append(text)
            self.in_p = False

    def handle_data(self, data):
        if self.in_p and not self.skip:
            self.buf.append(data)


def resolve_url(link):
    """Google News links are redirects; decode them to the publisher's URL."""
    if urlparse(link).netloc.endswith("news.google.com"):
        try:
            from googlenewsdecoder import gnewsdecoder

            return gnewsdecoder(link, interval=1).get("decoded_url") or None
        except Exception:
            return None
    return link


def fetch_text(link):
    """Return the article's main text (up to MAX_CHARS), or '' if it can't be read."""
    url = resolve_url(link)
    if not url:
        return ""
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en"}, timeout=20)
        if not r.ok or "html" not in r.headers.get("content-type", ""):
            return ""
        parser = _Paragraphs()
        parser.feed(r.text)
    except (requests.RequestException, ValueError):
        return ""
    text, seen = "", set()
    for p in parser.paragraphs:
        if p in seen:
            continue
        seen.add(p)
        text += p + "\n"
        if len(text) >= MAX_CHARS:
            break
    return text.strip()
