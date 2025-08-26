from utils.social_crawler import crawl_social_data
from utils.storage import save_posts, load_posts
import yfinance as yf
import os, json
from collections import Counter

def analyze_data():
    new_posts = crawl_social_data()
    save_posts(new_posts)
    all_posts = load_posts()

    tickers = set()
    for p in new_posts:
        for word in p.get("data", "").split():
            if word.isupper() and 1 <= len(word) <= 5:
                tickers.add(word)

    results = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="1mo")
            if hist.empty: continue
            change = (hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0] * 100
            pe = info.get("trailingPE")
            rec = info.get("recommendationMean")
            if change > -5 and pe and pe < 15 and rec and rec < 3:
                results.append({"ticker": t, "change_1mo": change, "pe": pe, "recommend": True})
        except:
            continue

    with open("data/analysis.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
