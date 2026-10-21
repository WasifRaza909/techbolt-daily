import calendar
import hashlib
import html
import re
import time

import feedparser

FEEDS = [
    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=gadgets+OR+smartphone+OR+startup+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
]


def _norm(title):
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def story_id(title):
    return hashlib.sha1(_norm(title).encode()).hexdigest()[:12]


def _clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def fetch_stories(posted_ids, max_age_hours=24):
    """Return recent, not-yet-posted stories, newest first."""
    cutoff = time.time() - max_age_hours * 3600
    seen, stories = set(posted_ids), []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if not getattr(e, "published_parsed", None):
                continue
            ts = calendar.timegm(e.published_parsed)
            if ts < cutoff:
                continue
            title = _clean(e.get("title"))
            source = (e.get("source") or {}).get("title") or feed.feed.get("title", "")
            # Google News appends " - Publisher" to titles
            if " - " in title:
                title, _, suffix = title.rpartition(" - ")
                source = source or suffix
            sid = story_id(title)
            if sid in seen:
                continue
            seen.add(sid)
            stories.append({
                "id": sid,
                "title": title,
                "summary": _clean(e.get("summary"))[:400],
                "source": source,
                "link": e.get("link", ""),
                "ts": ts,
            })
    stories.sort(key=lambda s: s["ts"], reverse=True)
    return stories
