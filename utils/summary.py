# utils/summary.py
import os, json
from typing import List

# Try to import format_quote; fallback if absent
try:
    from .analysis import fetch_quote, format_quote
except Exception:
    from .analysis import fetch_quote
    format_quote = None  # type: ignore

def _fmt(x, suf=""): 
    return "-" if x is None else (f"{x:.2f}{suf}" if isinstance(x,(int,float)) else str(x))

INDEXES = ["SPY","QQQ","DIA"]
SECTORS = ["XLK","XLF","XLE","XLY","XLP","XLV","XLI","XLB","XLRE","XLU","XLC"]

def market_snapshot() -> str:
    lines = ["【美股大盤】"]
    idx = [fetch_quote(t) for t in INDEXES]
    lines += [f"{q['ticker']}: {_fmt(q.get('chg_1d_pct'),'%')} (1D), {_fmt(q.get('chg_1m_pct'),'%')} (1M)" for q in idx]
    lines.append("")
    secs = [fetch_quote(t) for t in SECTORS]
    secs = sorted(secs, key=lambda x: (x.get("chg_1d_pct") or -999), reverse=True)
    top = ", ".join([f"{q['ticker']} {_fmt(q.get('chg_1d_pct'),'%')}" for q in secs[:5]])
    bot = ", ".join([f"{q['ticker']} {_fmt(q.get('chg_1d_pct'),'%')}" for q in secs[-5:]])
    lines.append("【板塊強弱（1D）】")
    lines.append(f"強：{top}")
    lines.append(f"弱：{bot}")
    return "\n".join(lines)

def pick_from_social(max_picks: int = 3) -> List[str]:
    path = os.path.join("data","social_posts.json")
    if not os.path.exists(path): return []
    try:
        with open(path,"r",encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    picks = []
    for item in data:
        for q in (item.get("analysis") or {}).get("quotes", []):
            if q.get("recommend"):
                Q = fetch_quote(q["ticker"])  # refresh
                if callable(format_quote):
                    picks.append(format_quote(Q))  # type: ignore
                else:
                    picks.append(f"{Q.get('ticker')} ${_fmt(Q.get('price'))} 1D {_fmt(Q.get('chg_1d_pct'),' %')} 1M {_fmt(Q.get('chg_1m_pct'),' %')} PE {_fmt(Q.get('pe'))}")
                if len(picks) >= max_picks:
                    return picks
    return picks

def daily_summary_text() -> str:
    lines = [market_snapshot(),""]
    recs = pick_from_social(3)
    if recs:
        lines.append("【今日關注】")
        lines += ["- "+r for r in recs]
    else:
        lines.append("【今日關注】暫無符合條件的社群推薦。")
    return "\n".join(lines)[:1800]
