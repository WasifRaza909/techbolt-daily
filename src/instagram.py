import os
import time

import requests

GRAPH = "https://graph.facebook.com/v21.0"


def _post(path, **data):
    data["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.post(f"{GRAPH}/{path}", data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text[:300]}")
    return r.json()


def _wait_until_ready(container_id):
    for _ in range(30):
        r = requests.get(
            f"{GRAPH}/{container_id}",
            params={"fields": "status_code", "access_token": os.environ["IG_ACCESS_TOKEN"]},
            timeout=30,
        )
        status = r.json().get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} status {status}")
        time.sleep(5)
    raise RuntimeError(f"Container {container_id} not ready in time")


def wait_for_urls(urls):
    """Raw GitHub URLs can lag a few seconds after a push."""
    for url in urls:
        for _ in range(18):
            r = requests.head(url, timeout=15, allow_redirects=True)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                break
            time.sleep(10)
        else:
            raise RuntimeError(f"Image not publicly reachable: {url}")


def publish_carousel(image_urls, caption):
    user = os.environ["IG_USER_ID"]
    wait_for_urls(image_urls)
    children = [_post(f"{user}/media", image_url=u, is_carousel_item="true")["id"] for u in image_urls]
    for c in children:
        _wait_until_ready(c)
    parent = _post(f"{user}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    _wait_until_ready(parent)
    return _post(f"{user}/media_publish", creation_id=parent)["id"]
