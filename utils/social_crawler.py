import os, re, json, requests
from datetime import datetime
from bs4 import BeautifulSoup
from analyzer import analyze_text

FB_TOKEN = os.environ.get("FB_PAGE_TOKEN")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ✅ 固定社群來源清單（支援 Facebook Page ID 或 Substack handle）
SOCIAL_CONFIG = [
    {"type": "facebook", "page_id": "103865129162015"},  # 替代 share ID: 16gt5rCZJD
    {"type": "facebook", "page_id": "61557939115453"},   # 替代 share ID: 1D9kKbnNDs
    {"type": "substack", "handle": "unclestocknotes"},
    {"type": "substack", "handle": "skilleddriver"}
]

def fetch_facebook_posts(page_id, limit=2):
    url = f"https://graph.facebook.com/v17.0/{page_id}/posts"
    r = requests.get(url, params={
        "access_token": FB_TOKEN,
        "fields": "message,created_time,permalink_url",
        "limit": limit
    })
    posts = r.json().get("data", [])
    return [{
        "text": post.get("message", "").strip(),
        "time": post.get("created_time", ""),
        "url": post.get("permalink_url", "")
    } for post in posts if post.get("message")]

def fetch_substack_posts(handle, limit=2):
    url = f"https://{handle}.substack.com/feed"
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "xml")
    items = soup.find_all("item")[:limit]
    results = []
    for item in items:
        title = item.title.string if item.title else ""
        desc = item.description.string if item.description else ""
        link = item.link.string if item.link else ""
        date = item.pubDate.string if item.pubDate else ""
        results.append({
            "text": f"{title}\n{desc}",
            "time": date,
            "url": link
        })
    return results

def clean_text(text):
    return re.sub(r"http\S+|\n+", " ", text).strip()

def crawl_social_data():
    results = []
    for cfg in SOCIAL_CONFIG:
        try:
            if cfg["type"] == "facebook":
                posts = fetch_facebook_posts(cfg["page_id"])
                for p in posts:
                    cleaned = clean_text(p["text"])
                    analysis = analyze_text(cleaned)
                    results.append({
                        "source": f"Facebook {cfg['page_id']}",
                        "text": cleaned,
                        "url": p["url"],
                        "time": p["time"],
                        "analysis": analysis
                    })
            elif cfg["type"] == "substack":
                posts = fetch_substack_posts(cfg["handle"])
                for p in posts:
                    cleaned = clean_text(p["text"])
                    analysis = analyze_text(cleaned)
                    results.append({
                        "source": f"Substack {cfg['handle']}",
                        "text": cleaned,
                        "url": p["url"],
                        "time": p["time"],
                        "analysis": analysis
                    })
        except Exception as e:
            results.append({
                "source": cfg.get("page_id") or cfg.get("handle"),
                "text": f"[抓取失敗: {e}]",
                "url": "",
                "time": datetime.utcnow().isoformat(),
                "analysis": {}
            })
    os.makedirs("data", exist_ok=True)
    with open("data/social_posts.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results
