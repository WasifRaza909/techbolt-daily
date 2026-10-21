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
gadgets, money, or something that affects everyday people. Prefer concrete news: launches, \
deals, numbers, policy changes, product updates, security issues. Avoid opinion pieces, \
interviews, "CEO says" predictions, listicles, shopping deals, press-release fluff and local \
stories. Prefer well-known publishers. Then write the post.

Rules:
- Use ONLY facts present in the title/snippet. Do not invent numbers, quotes or details.
- Write everything in your own words. Never copy the source headline or any sentence from the snippet verbatim, and never put any words in quotation marks.
- Attribute claims to the publisher (for example "according to <source>" or "<source> reports") when the story is a report, rumour, leak or allegation. Never state rumours or allegations as fact.
- Do not accuse or speculate about named private individuals or make legal, medical or investment claims. Skip stories about crimes, lawsuits against individuals, tragedies, minors, or adult content and pick another story.
- No promises about prices, stocks or returns, and no predictions presented as fact.
- Plain, punchy language. No clickbait lies, no emojis in the headline.
- headline: max 8 words, written to stop the scroll.
- highlight: the 1-3 most important words of the headline, copied exactly from it.
- category: ONE word in caps, no commas, such as AI, GADGETS, STARTUPS, SECURITY, BUSINESS, SPACE, GAMING.
- points: {points_rule}
- caption: first line is a hook (max 12 words), then 2-3 short sentences explaining why it matters.
- question: one short question that invites comments.
- hashtags: 7 relevant hashtags without the # symbol (mix broad and niche).

Return JSON: {{"pick": int, "headline": str, "highlight": str, "category": str, "points": [str],"caption": str, \
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


POINTS_FIXED = "exactly 3 short takeaways, each max 16 words."
POINTS_VARIABLE = (
    "2 to 8 short takeaways, each max 16 words. Use as many as the story genuinely has substance "
    "for: a thin story gets 2 or 3, a big story with many distinct facts gets 5 to 8. Never pad."
)


def write_post(stories, recent_headlines, variable=False):
    stories = stories[:30]
    candidates = "\n".join(
        f"{i} | {s['title']} | {s['source']} | {s['summary']}" for i, s in enumerate(stories)
    )
    recent = "\n".join(f"- {h}" for h in recent_headlines[-15:]) or "(none)"
    rule = POINTS_VARIABLE if variable else POINTS_FIXED
    data = json.loads(_call(PROMPT.format(candidates=candidates, recent=recent, points_rule=rule)))
    story = stories[int(data["pick"])]
    assert len(data["points"]) >= 2 and data["headline"] and data["caption"]
    return story, data
