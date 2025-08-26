import re
_TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")
def analyze_text(text: str) -> dict:
    tickers = list({m.group(0) for m in _TICKER_RE.finditer(text or "")})
    recommend = bool(tickers) and any(k in (text or "").upper() for k in ["BUY","ADD","ACCUMULATE","看多","加碼","買進"])
    return {"tickers": tickers[:5], "recommend": recommend, "note": "lightweight analysis (no network calls)."}
