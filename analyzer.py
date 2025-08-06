from utils.social_crawler import crawl_social_data
from utils.storage import save_posts, load_posts
import yfinance as yf
import os, json
from collections import Counter

def analyze_data():
    # Crawl and store posts
    new_posts = crawl_social_data()
    save_posts(new_posts)
    all_posts = load_posts()

    # Auto-track sources with >2 posts
    url_counts = Counter([p['url'] for p in all_posts])
    auto_tracked = [url for url, cnt in url_counts.items() if cnt > 2]

    # Extract potential tickers (uppercase words <=5 chars)
    tickers = set()
    for p in new_posts:
        for word in p.get('data', '').split():
            if word.isupper() and len(word) <= 5:
                tickers.add(word)

    analysis_results = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period='1mo')
        if hist.empty:
            continue
        change_1mo = (hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0] * 100
        pe = info.get('trailingPE')
        recommendation = info.get('recommendationMean')
        recommend = False
        # Conditions: not dropped >5%, P/E <15, recommendation <3
        if change_1mo > -5 and pe and pe < 15 and recommendation and recommendation < 3:
            recommend = True
        analysis_results.append({
            'ticker': ticker,
            'change_1mo': change_1mo,
            'pe': pe,
            'recommendation': recommendation,
            'auto_tracked': ticker in auto_tracked,
            'recommend': recommend
        })

    # Save analysis
    os.makedirs('data', exist_ok=True)
    with open(os.path.join('data', 'analysis.json'), 'w') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)