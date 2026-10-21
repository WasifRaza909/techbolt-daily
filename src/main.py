"""Usage: python -m src.main generate | publish"""
import json
import os
import shutil
import sys
import time

from . import ai, images, instagram, news

POSTED = "posted.json"
PENDING = "out/pending.json"
POSTS_DIR = "posts"
HANDLE = os.environ.get("BRAND_HANDLE") or "@yourpage"
if not HANDLE.startswith("@"):
    HANDLE = "@" + HANDLE


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _save(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _prune_old_posts(keep_days=2):
    """Published images only need to exist long enough for Instagram to fetch them."""
    if not os.path.isdir(POSTS_DIR):
        return
    cutoff = time.time() - keep_days * 86400
    for name in os.listdir(POSTS_DIR):
        path = os.path.join(POSTS_DIR, name)
        if os.path.getmtime(path) < cutoff:
            shutil.rmtree(path, ignore_errors=True)


def build_caption(story, data):
    tags = " ".join("#" + t.lstrip("#").replace(" ", "") for t in data["hashtags"][:8])
    return (
        f"{data['caption']}\n\n"
        f"{data['question']}\n\n"
        f"Save this for later and follow {HANDLE} for daily tech news.\n"
        f"Source: {story['source']}\n\n"
        f"{tags}"
    )


def generate():
    posted = _load(POSTED, [])
    stories = news.fetch_stories([p["id"] for p in posted])
    if not stories:
        sys.exit("No fresh stories found.")
    story, data = ai.write_post(stories, [p["headline"] for p in posted])

    folder = f"{time.strftime('%Y%m%d-%H%M')}-{story['id'][:6]}"
    out_dir = os.path.join(POSTS_DIR, folder)
    paths = images.build_slides(data, HANDLE, out_dir)
    caption = build_caption(story, data)

    _save(PENDING, {
        "story_id": story["id"],
        "headline": data["headline"],
        "link": story["link"],
        "caption": caption,
        "images": [p.replace("\\", "/") for p in paths],
    })
    _prune_old_posts()
    print(f"Generated: {data['headline']}\n\n{caption}\n\nImages in {out_dir}")


def publish():
    if os.environ.get("DRY_RUN", "true").lower() != "false":
        print("DRY_RUN is on: skipping publish.")
        return
    pending = _load(PENDING, None)
    if not pending:
        sys.exit("Nothing pending. Run generate first.")
    repo = os.environ["GITHUB_REPOSITORY"]
    ref = os.environ.get("GITHUB_REF_NAME", "main")
    urls = [f"https://raw.githubusercontent.com/{repo}/{ref}/{p}" for p in pending["images"]]
    media_id = instagram.publish_carousel(urls, pending["caption"])

    posted = _load(POSTED, [])
    posted.append({
        "id": pending["story_id"],
        "headline": pending["headline"],
        "link": pending["link"],
        "ig_media_id": media_id,
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _save(POSTED, posted[-300:])
    print(f"Published {media_id}")


if __name__ == "__main__":
    {"generate": generate, "publish": publish}[sys.argv[1]]()
