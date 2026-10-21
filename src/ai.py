import json
import os
import time

import requests

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = """You run a popular Instagram page that posts daily tech news for a general audience.

Candidate stories (index | title | source | snippet):
{candidates}

Headlines we already posted recently (do NOT pick the same topic):
{recent}

Pick the ONE story most likely to get saves, shares and follows: big companies, AI, \
gadgets, money, or something that affects everyday people. Then write the post.

Rules:
- Use ONLY facts present in the title/snippet. Do not invent numbers, quotes or details.
- Plain, punchy language. No clickbait lies, no emojis in the headline.
- headline: max 8 words, written to stop the scroll.
- highlight: the 1-3 most important words of the headline, copied exactly from it.
- category: one or two words in caps, such as AI, GADGETS, STARTUPS, SECURITY, BUSINESS, SPACE, GAMING.
- points: exactly 3 short takeaways, each max 16 words.
- caption: first line is a hook (max 12 words), then 2-3 short sentences explaining why it matters.
- question: one short question that invites comments.
- hashtags: 7 relevant hashtags without the # symbol (mix broad and niche).

Return JSON: {{"pick": int, "headline": str, "highlight": str, "category": str, "points": [str,str,str], "caption": str, \
"question": str, "hashtags": [str]}}"""


def _call(prompt):
    key = os.environ["GEMINI_API_KEY"]
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
    }
    for attempt in range(4):
        r = requests.post(URL, json=body, headers={"x-goog-api-key": key}, timeout=60)
        if r.status_code in (429, 500, 503):
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError(f"Gemini failed after retries: {r.status_code} {r.text[:200]}")


def write_post(stories, recent_headlines):
    stories = stories[:30]
    candidates = "\n".join(
        f"{i} | {s['title']} | {s['source']} | {s['summary']}" for i, s in enumerate(stories)
    )
    recent = "\n".join(f"- {h}" for h in recent_headlines[-15:]) or "(none)"
    data = json.loads(_call(PROMPT.format(candidates=candidates, recent=recent)))
    story = stories[int(data["pick"])]
    assert len(data["points"]) >= 3 and data["headline"] and data["caption"]
    return story, data
