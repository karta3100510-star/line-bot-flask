# utils/social_crawler.py
import os
import re
import json
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

from utils.analysis import analyze_text

FB_TOKEN = os.environ.get("FB_PAGE_TOKEN", "")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# 你可以在這裡調整來源
SOCIAL_CONFIG = [
    {"type": "facebook", "page_id": "16gt5rCZJD"},   # 支援 share id / 數字 id / 完整連結
    {"type": "substack", "handle": "unclestocknotes"},
]

def _clean_text(t: str) -> str:
    t = (t or "").replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t)
    return re.sub(r"http\S+", "", t).strip()

def _soup(xml_text: str) -> BeautifulSoup:
    for parser in ("lxml-xml", "xml", "html.parser"):
        try:
            return BeautifulSoup(xml_text, parser)
        except Exception:
            continue
    return BeautifulSoup(xml_text, "html.parser")

# ---------- Facebook helpers ----------
def _resolve_share_id_to_final_url(share_id: str) -> str:
    try:
        url = f"https://www.facebook.com/share/{share_id}/"
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.url
    except Exception:
        return ""

def _graph_lookup_og_object_id(url: str) -> str:
    if not FB_TOKEN:
        return ""
    try:
        resp = requests.get(
            "https://graph.facebook.com/v17.0/",
            params={"id": url, "fields": "og_object{id}", "access_token": FB_TOKEN},
            timeout=10,
        )
        data = resp.json()
        ogid = (((data or {}).get("og_object") or {}).get("id")) or ""
        if "_" in ogid:
            return ogid.split("_")[0]
        return ogid if ogid.isdigit() else ""
    except Exception:
        return ""

def _graph_post_to_page_id(post_id: str) -> str:
    if not FB_TOKEN:
        return ""
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v17.0/{post_id}",
            params={"fields": "from", "access_token": FB_TOKEN},
            timeout=10,
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
        parts = [p for p in u.path.split("/") if p]
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
    # 1) already numeric id
    if str(src).isdigit():
        return src, "numeric id"
    # 2) share id
    final_url = _resolve_share_id_to_final_url(src)
    if final_url:
        pid = _extract_page_id_from_url(final_url) or _graph_lookup_og_object_id(final_url)
        if pid:
            return pid, f"resolved from share '{src}'"
    # 3) direct url
    if str(src).startswith("http"):
        pid = _graph_lookup_og_object_id(src)
        if pid:
            return pid, "resolved from url"
    return "", f"cannot resolve '{src}' to page id"

def fetch_facebook_posts(page_id_or_share: str, limit: int = 2):
    page_id, note = _normalize_facebook_source_to_page_id(page_id_or_share)
    if not page_id:
        return [], f"Invalid facebook source ({note})."
    if not FB_TOKEN:
        return [], "FB_PAGE_TOKEN not set."
    url = f"https://graph.facebook.com/v17.0/{page_id}/posts"
    try:
        r = requests.get(
            url,
            params={"access_token": FB_TOKEN, "fields": "message,created_time,permalink_url", "limit": limit},
            timeout=12,
        )
        data = r.json()
        posts = data.get("data", []) if isinstance(data, dict) else []
        out = []
        for p in posts:
            msg = _clean_text(p.get("message", ""))
            if not msg:
                continue
            out.append(
                {
                    "text": msg,
                    "time": p.get("created_time", ""),
                    "url": p.get("permalink_url", ""),
                }
            )
        if not out:
            return [], f"No posts (page_id={page_id})."
        return out, note or None
    except Exception as e:
        return [], f"FB fetch error: {e}"

# ---------- Substack ----------
def fetch_substack_posts(handle: str, limit: int = 2):
    url = f"https://{handle}.substack.com/feed"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        soup = _soup(r.text)
        items = soup.find_all("item")[:limit]
        results = []
        for it in items:
            title = (it.title.string if it and it.title else "") or ""
            desc = (it.description.string if it and it.description else "") or ""
            link = (it.link.string if it and it.link else "") or ""
            date = (it.pubDate.string if it and it.pubDate else "") or ""
            text = _clean_text(f"{title} {desc}")[:500]
            if not text and link:
                text = link
            if not text:
                text = "[no text]"
            results.append({"text": text, "time": date, "url": link})
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
                posts, note = fetch_facebook_posts(cfg["page_id"])
                if isinstance(note, str) and note:
                    results.append(
                        {
                            "source": f"Facebook {cfg['page_id']}",
                            "text": f"[info: {note}]",
                            "url": "",
                            "time": datetime.utcnow().isoformat(),
                            "analysis": {},
                        }
                    )
                if not posts:
                    results.append(
                        {
                            "source": f"Facebook {cfg['page_id']}",
                            "text": "[No posts]",
                            "url": "",
                            "time": datetime.utcnow().isoformat(),
                            "analysis": {},
                        }
                    )
                for p in posts:
                    analysis = analyze_text(p["text"])
                    results.append(
                        {
                            "source": f"Facebook {cfg['page_id']}",
                            "text": p["text"],
                            "url": p["url"],
                            "time": p["time"],
                            "analysis": analysis,
                        }
                    )
            elif cfg["type"] == "substack":
                posts, err = fetch_substack_posts(cfg["handle"])
                if err:
                    results.append(
                        {
                            "source": f"Substack {cfg['handle']}",
                            "text": f"[{err}]",
                            "url": "",
                            "time": datetime.utcnow().isoformat(),
                            "analysis": {},
                        }
                    )
                for p in posts:
                    analysis = analyze_text(p["text"])
                    results.append(
                        {
                            "source": f"Substack {cfg['handle']}",
                            "text": p["text"],
                            "url": p["url"],
                            "time": p["time"],
                            "analysis": analysis,
                        }
                    )
        except Exception as e:
            results.append(
                {
                    "source": cfg.get("page_id") or cfg.get("handle"),
                    "text": f"[抓取失敗: {e}]",
                    "url": "",
                    "time": datetime.utcnow().isoformat(),
                    "analysis": {},
                }
            )

    # 永遠寫檔（讓 /social 能讀到）
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/social_posts.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[crawl] write file failed:", e)

    return results
