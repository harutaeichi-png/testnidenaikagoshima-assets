"""Post queued items to Instagram via the Instagram API with Instagram Login.

Each run posts every item in queue.json whose date (JST) is today or earlier
and whose id is not yet in posted.json, oldest first, as a 2-image carousel.
"""
import json, os, sys, time, datetime as dt, urllib.parse, urllib.request

API = "https://graph.instagram.com/v23.0"
TOKEN = os.environ["IG_TOKEN"]
RAW = "https://raw.githubusercontent.com/{}/main/".format(os.environ["GITHUB_REPOSITORY"])
JST = dt.timezone(dt.timedelta(hours=9))
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "10"))
DRY = os.environ.get("DRY_RUN") == "1"


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code} on {path}: {e.read().decode()[:500]}")


def wait_ready(cid):
    for _ in range(30):
        s = call("GET", cid, fields="status_code").get("status_code")
        if s == "FINISHED":
            return
        if s == "ERROR":
            sys.exit(f"container {cid} failed")
        time.sleep(5)
    sys.exit(f"container {cid} not ready")


def post(item):
    children = []
    for p in item["images"]:
        c = call("POST", "me/media", image_url=RAW + p, is_carousel_item="true")["id"]
        wait_ready(c)
        children.append(c)
    parent = call("POST", "me/media", media_type="CAROUSEL",
                  children=",".join(children), caption=item["caption"])["id"]
    wait_ready(parent)
    return call("POST", "me/media_publish", creation_id=parent)["id"]


def main():
    queue = json.load(open("queue.json"))
    posted = json.load(open("posted.json"))
    today = dt.datetime.now(JST).date().isoformat()
    due = [q for q in queue if q["date"] <= today and q["id"] not in posted][:MAX_PER_RUN]
    print(f"today={today} due={len(due)}")
    if DRY:
        for q in due:
            print("would post", q["id"], q["word"])
        return
    # keep the long-lived token alive (extends expiry when older than 24h)
    try:
        urllib.request.urlopen("https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=" + TOKEN, timeout=30)
    except Exception as e:
        print("token refresh skipped:", e)
    for q in due:
        mid = post(q)
        posted.append(q["id"])
        json.dump(posted, open("posted.json", "w"))
        print("posted", q["id"], q["word"], mid)
        time.sleep(20)


if __name__ == "__main__":
    main()
