import os, requests
from bs4 import BeautifulSoup

FB_TOKEN = os.environ.get("FB_PAGE_TOKEN")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SOCIAL_CONFIG = [
    {"type": "facebook", "page_id": "16gt5rCZJD"},
    {"type": "substack", "handle": "unclestocknotes"}
]

def fetch_facebook(page_id):
    url = f"https://graph.facebook.com/v17.0/{page_id}/posts"
    r = requests.get(url, params={
        "access_token": FB_TOKEN,
        "fields": "message,created_time,permalink_url",
        "limit": 1
    })
    data = r.json().get("data", [])
    if not data:
        return "No posts"
    return data[0].get("message", "")[:200]

def fetch_substack(handle):
    url = f"https://{handle}.substack.com/feed"
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "xml")
    item = soup.find("item")
    return item.title.string if item and item.title else "No post"

def crawl_social_data():
    results = []
    for cfg in SOCIAL_CONFIG:
        try:
            if cfg["type"] == "facebook":
                content = fetch_facebook(cfg["page_id"])
                results.append({"source": f"Facebook {cfg['page_id']}", "data": content})
            elif cfg["type"] == "substack":
                content = fetch_substack(cfg["handle"])
                results.append({"source": f"Substack {cfg['handle']}", "data": content})
        except Exception as e:
            results.append({"source": cfg.get("page_id") or cfg.get("handle"), "data": f"[抓取失敗: {e}]"})
    return results
