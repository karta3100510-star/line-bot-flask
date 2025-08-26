import os, re, json, requests
from datetime import datetime
from bs4 import BeautifulSoup
from analyzer import analyze_text

FB_TOKEN = os.environ.get("FB_PAGE_TOKEN")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SOCIAL_CONFIG = [
    {"type": "facebook", "page_id": "103865129162015"},
    {"type": "substack", "handle": "unclestocknotes"}
]

def _clean_text(t: str) -> str:
    return re.sub(r"http\S+|\s+", " ", (t or "")).strip()

def _parse_xml_with_fallback(xml_text: str) -> BeautifulSoup:
    for parser in ("lxml-xml", "xml", "html.parser"):
        try:
            return BeautifulSoup(xml_text, parser)
        except Exception:
            continue
    return BeautifulSoup(xml_text, "html.parser")

def fetch_facebook_posts(page_id: str, limit: int = 2):
    if not page_id.isdigit():
        return [], f"Invalid page_id '{page_id}'. Use numeric Facebook Page ID."

    url = f"https://graph.facebook.com/v17.0/{page_id}/posts"
    try:
        r = requests.get(url, params={
            "access_token": FB_TOKEN,
            "fields": "message,created_time,permalink_url",
            "limit": limit
        }, timeout=10)
        r.raise_for_status()
        posts = r.json().get("data", [])
        data = [{
            "text": _clean_text(p.get("message", "")),
            "time": p.get("created_time", ""),
            "url": p.get("permalink_url", ""),
        } for p in posts if p.get("message")]
        if not data:
            return [], "No posts (check token permission or page activity)."
        return data, None
    except Exception as e:
        return [], f"FB fetch error: {e}"

def fetch_substack_posts(handle: str, limit: int = 2):
    url = f"https://{handle}.substack.com/feed"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = _parse_xml_with_fallback(r.text)
        items = soup.find_all("item")[:limit]
        results = []
        for it in items:
            title = (it.title.string if it and it.title else "") or ""
            desc = (it.description.string if it and it.description else "") or ""
            link = (it.link.string if it and it.link else "") or ""
            date = (it.pubDate.string if it and it.pubDate else "") or ""
            results.append({
                "text": _clean_text(f"{title} {desc}"),
                "time": date,
                "url": link
            })
        if not results:
            return [], "No items in feed."
        return results, None
    except Exception as e:
        return [], f"RSS error: {e}"

def crawl_social_data():
    results = []
    for cfg in SOCIAL_CONFIG:
        try:
            if cfg["type"] == "facebook":
                posts, err = fetch_facebook_posts(cfg["page_id"])
                if err:
                    results.append({
                        "source": f"Facebook {cfg['page_id']}",
                        "text": f"[{err}]",
                        "url": "",
                        "time": datetime.utcnow().isoformat(),
                        "analysis": {}
                    })
                for p in posts:
                    analysis = analyze_text(p["text"])
                    results.append({
                        "source": f"Facebook {cfg['page_id']}",
                        "text": p["text"],
                        "url": p["url"],
                        "time": p["time"],
                        "analysis": analysis
                    })
            elif cfg["type"] == "substack":
                posts, err = fetch_substack_posts(cfg["handle"])
                if err:
                    results.append({
                        "source": f"Substack {cfg['handle']}",
                        "text": f"[{err}]",
                        "url": "",
                        "time": datetime.utcnow().isoformat(),
                        "analysis": {}
                    })
                for p in posts:
                    analysis = analyze_text(p["text"])
                    results.append({
                        "source": f"Substack {cfg['handle']}",
                        "text": p["text"],
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
