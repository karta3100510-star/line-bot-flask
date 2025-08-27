# utils/analysis.py
import re, time
from typing import Dict, Any, List

_yf = None  # lazy import yfinance
_CACHE: Dict[str, Any] = {}
_TTL = 300  # seconds
_TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")

def _now() -> float: return time.time()

def _cache_get(key: str):
    it = _CACHE.get(key)
    if not it: return None
    ts, ttl, val = it
    if _now() - ts < ttl: return val
    _CACHE.pop(key, None); return None

def _cache_set(key: str, val, ttl: int = _TTL): _CACHE[key] = (_now(), ttl, val)

def _import_yf():
    global _yf
    if _yf is None:
        import yfinance as yf
        _yf = yf
    return _yf

def _safe_float(x):
    try:
        if x is None: return None
        return float(x)
    except Exception:
        return None

def _pct(a, b):
    try:
        if a in (None, 0): return None
        return (b - a) / a * 100.0
    except Exception:
        return None

def extract_tickers(text: str) -> List[str]:
    seen, out = set(), []
    for m in _TICKER_RE.finditer(text or ""):
        t = m.group(0).upper()
        if t not in seen:
            seen.add(t); out.append(t)
    return out[:5]

def fetch_quote(ticker: str) -> Dict[str, Any]:
    key = f"q:{ticker}"
    c = _cache_get(key)
    if c is not None: return c
    yf = _import_yf()
    info = {"ticker": ticker}
    try:
        t = yf.Ticker(ticker)
        d = t.history(period="5d", interval="1d", auto_adjust=False)
        if not d.empty:
            last = float(d["Close"].iloc[-1])
            prev = float(d["Close"].iloc[-2]) if len(d) >= 2 else None
            info["price"] = last
            info["chg_1d_pct"] = _pct(prev, last) if prev is not None else None
        m = t.history(period="1mo", interval="1d", auto_adjust=False)
        if not m.empty:
            first = float(m["Close"].iloc[0]); lastm = float(m["Close"].iloc[-1])
            info["chg_1m_pct"] = _pct(first, lastm)
        pe = None
        try:
            fi = getattr(t, "fast_info", {}); pe = float(fi.get("trailingPe"))
        except Exception: pe = None
        if pe is None:
            try: pe = float(getattr(t, "info", {}).get("trailingPE"))
            except Exception: pe = None
        info["pe"] = pe
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
    _cache_set(key, info, ttl=180); return info

def rule_of_thumb(q: Dict[str, Any]) -> Dict[str, Any]:
    pe, m1, d1 = q.get("pe"), q.get("chg_1m_pct"), q.get("chg_1d_pct")
    reason = []
    if m1 is not None and m1 >= 5: reason.append("1M momentum >= 5%")
    if pe is not None and 5 <= pe <= 40: reason.append("PE in 5~40")
    if d1 is not None and d1 >= 0: reason.append("green day")
    return {"recommend": len(reason) >= 2, "reason": reason}

def format_quote(q: Dict[str, Any]) -> str:
    def _fmt(x, suf=""): 
        return "-" if x is None else (f"{x:.2f}{suf}" if isinstance(x,(int,float)) else str(x))
    s = f"{q.get('ticker','')} | ${_fmt(q.get('price'))} | 1D {_fmt(q.get('chg_1d_pct'),' %')} | 1M {_fmt(q.get('chg_1m_pct'),' %')} | PE {_fmt(q.get('pe'))}"
    rec = rule_of_thumb(q)
    if rec.get("recommend"):
        s += " → ✅ 建議觀察/買入（" + ", ".join(rec.get("reason", [])) + "）"
    else:
        reasons = rec.get("reason", [])
        if reasons: s += " → ⚠️ " + ", ".join(reasons)
    return s

def analyze_text(text: str) -> Dict[str, Any]:
    tickers = extract_tickers(text)
    quotes = []
    for t in tickers:
        q = fetch_quote(t); rec = rule_of_thumb(q)
        quotes.append({"ticker": t, **q, **rec})
    return {"tickers": tickers, "quotes": quotes}
