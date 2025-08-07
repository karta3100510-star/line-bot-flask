# utils/social_crawler.py

import requests
from bs4 import BeautifulSoup

SOCIAL_URLS = [
    # 你的各条链接……
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_facebook(url):
    # 改用 m.facebook.com
    mobile = url.replace("www.facebook.com", "m.facebook.com")
    resp = requests.get(mobile, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        return og["content"]
    # fallback：取正文 snippet
    text = soup.get_text(separator=" ", strip=True)
    return text[:200] + "…"

def fetch_substack(url):
    # 试着读 RSS
    feed_url = url.rstrip("/") + "/feed"
    resp = requests.get(feed_url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "xml")
    item = soup.find("item")
    if item and item.title:
        return item.title.string
    return "No recent post."

def crawl_social_data():
    results = []
    for url in SOCIAL_URLS:
        try:
            if "facebook.com" in url:
                summary = fetch_facebook(url)
            elif "substack.com" in url:
                summary = fetch_substack(url)
            else:
                # 通用处理
                resp = requests.get(url, headers=HEADERS, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                og = soup.find("meta", property="og:description")
                summary = og["content"] if og and og.get("content") else soup.title.string or ""
            results.append({"url": url, "data": summary})
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            results.append({"url": url, "data": "[抓取失败]"})

    return results
