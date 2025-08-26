import os, requests
from bs4 import BeautifulSoup

FB_TOKEN = os.environ.get("FB_PAGE_TOKEN")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

from urllib.parse import urlparse, parse_qs

def _resolve_share_id_to_final_url(share_id: str) -> str:
    try:
        url = f"https://www.facebook.com/share/{share_id}/"
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.url
    except Exception:
        return ""

def _graph_lookup_og_object_id(url: str) -> str:
    try:
        resp = requests.get(
            "https://graph.facebook.com/v17.0/",
            params={"id": url, "fields": "og_object{id}", "access_token": FB_TOKEN},
            timeout=10
        )
        data = resp.json()
        ogid = (((data or {}).get("og_object") or {}).get("id")) or ""
        if "_" in ogid:
            return ogid.split("_")[0]
        return ""
    except Exception:
        return ""

def _graph_post_to_page_id(post_id: str) -> str:
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v17.0/{post_id}",
            params={"fields": "from", "access_token": FB_TOKEN},
            timeout=10
        )
        data = resp.json()
        frm = (data or {}).get("from") or {}
        pid = str(frm.get("id", ""))
        return pid if pid.isdigit() else ""
    except Exception:
        return ""

def _extract_page_id_from_url(final_url: str) -> str:
    try:
        if not final_url:
            return ""
        u = urlparse(final_url)
        qs = parse_qs(u.query)
        if "id" in qs and qs["id"]:
            pid = qs["id"][0]
            if pid.isdigit():
                return pid
        parts = [p for p in u.path.split('/') if p]
        if "posts" in parts:
            idx = parts.index("posts")
            if idx + 1 < len(parts):
                post_id = parts[idx + 1]
                page_id = _graph_post_to_page_id(post_id)
                if page_id:
                    return page_id
        return ""
    except Exception:
        return ""

def _normalize_facebook_source_to_page_id(src: str):
    if str(src).isdigit():
        return src, ""
    final_url = _resolve_share_id_to_final_url(src)
    if final_url:
        pid = _extract_page_id_from_url(final_url)
        if pid:
            return pid, f"resolved from share '{src}'"
        pid = _graph_lookup_og_object_id(final_url)
        if pid:
            return pid, f"resolved via og_object from '{src}'"
    if str(src).startswith("http"):
        pid = _graph_lookup_og_object_id(src)
        if pid:
            return pid, "resolved from direct url"
    return "", f"cannot resolve '{src}' to numeric page id"



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
                        if isinstance(note, str) and note:
                results.append({
                    "source": f"Facebook {cfg['page_id']}",
                    "text": f"[info: {note}]",
                    "url": "",
                    "time": datetime.utcnow().isoformat(),
                    "analysis": {}
                })
            elif not posts:
                results.append({
                    "source": f"Facebook {cfg['page_id']}",
                    "text": f"[No posts]",
                    "url": "",
                    "time": datetime.utcnow().isoformat(),
                    "analysis": {}
                })
            elif cfg["type"] == "substack":
                content = fetch_substack(cfg["handle"])
                results.append({"source": f"Substack {cfg['handle']}", "data": content})
        except Exception as e:
            results.append({"source": cfg.get("page_id") or cfg.get("handle"), "data": f"[抓取失敗: {e}]"})
    return results
