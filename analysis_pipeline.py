import os
import math
import requests
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta, timezone
from dateutil import tz
from yahooquery import Ticker

TZ = tz.gettz("Asia/Taipei")
FINNHUB_TOKEN = os.environ.get("FINNHUB_TOKEN", "")
ALPHAVANTAGE_KEY = os.environ.get("ALPHAVANTAGE_KEY", "")

def _pct(a, b):
    try:
        return (a / b - 1.0) * 100.0
    except Exception:
        return None

def fetch_price_and_ta(ticker: str, lookback_days=250):
    yq = Ticker(ticker)
    hist = yq.history(period="1y")
    if isinstance(hist, pd.DataFrame) and not hist.empty:
        df = hist.reset_index()
        df = df.rename(columns={"date": "Date", "close": "Close", "high": "High",
                                "low": "Low", "open": "Open", "volume": "Volume"})
        df["SMA20"] = ta.sma(df["Close"], length=20)
        df["SMA50"] = ta.sma(df["Close"], length=50)
        df["SMA200"] = ta.sma(df["Close"], length=200)
        macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
        df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = macd["MACD_12_26_9"], macd["MACDs_12_26_9"], macd["MACDh_12_26_9"]
        df["RSI14"] = ta.rsi(df["Close"], length=14)
        bb = ta.bbands(df["Close"], length=20, std=2)
        df["BB_UP"], df["BB_MID"], df["BB_LOW"] = bb[bb.columns[0]], bb[bb.columns[1]], bb[bb.columns[2]]

        last = df.iloc[-1]
        close = float(last["Close"]) if not math.isnan(last["Close"]) else None
        sma50 = float(last["SMA50"]) if not math.isnan(last["SMA50"]) else None
        sma200 = float(last["SMA200"]) if not math.isnan(last["SMA200"]) else None
        rsi14 = float(last["RSI14"]) if not math.isnan(last["RSI14"]) else None
        fifty_two_w_low = float(df["Close"].min())
        fifty_two_w_high = float(df["Close"].max())
        trend = ("多頭" if (close and sma50 and sma200 and close> sma50> sma200) else
                 "整理" if (close and sma50 and sma200 and (min(close, sma50, sma200) < max(close, sma50, sma200) and not (close> sma50> sma200) and not (close< sma50< sma200))) else
                 "空頭")
        ta_summary = {
            "close": close,
            "sma50": sma50,
            "sma200": sma200,
            "rsi14": rsi14,
            "range52": (fifty_two_w_low, fifty_two_w_high),
            "trend": trend,
            "macd": float(last["MACD"]) if not math.isnan(last["MACD"]) else None,
            "macd_signal": float(last["MACD_SIGNAL"]) if not math.isnan(last["MACD_SIGNAL"]) else None,
            "bb_mid": float(last["BB_MID"]) if not math.isnan(last["BB_MID"]) else None
        }
        return df, ta_summary
    else:
        raise RuntimeError("Yahoo 資料取得失敗或代碼無效")

def fetch_fundamentals(ticker: str):
    yq = Ticker(ticker)
    key_stats = yq.key_stats
    summary = yq.summary_detail
    fin = yq.all_financial_data()

    pe = None
    if isinstance(summary, dict) and ticker.lower() in summary:
        pe = summary[ticker.lower()].get("trailingPE") or summary[ticker.lower()].get("forwardPE")
    mcap = None
    if isinstance(key_stats, dict) and ticker.lower() in key_stats:
        mcap = key_stats[ticker.lower()].get("marketCap")

    rev_growth = None
    if isinstance(fin, pd.DataFrame) and not fin.empty:
        fin = fin.reset_index()
        try:
            latest = fin.sort_values("asOfDate").iloc[-1]
            prev = fin.sort_values("asOfDate").iloc[-5]
            rev_growth = _pct(latest.get("TotalRevenue"), prev.get("TotalRevenue"))
        except Exception:
            pass

    return {
        "pe": pe,
        "mcap": mcap,
        "rev_growth_yoy": rev_growth
    }

def fetch_recent_news(ticker: str, limit=5):
    out = []
    if ALPHAVANTAGE_KEY:
        try:
            url = ("https://www.alphavantage.co/query"
                   f"?function=NEWS_SENTIMENT&tickers={ticker}&sort=LATEST&apikey={ALPHAVANTAGE_KEY}")
            r = requests.get(url, timeout=10)
            j = r.json()
            for it in j.get("feed", [])[:limit]:
                out.append({
                    "title": it.get("title"),
                    "url": it.get("url"),
                    "summary": (it.get("summary") or "")[:180]
                })
        except Exception:
            pass
    elif FINNHUB_TOKEN:
        try:
            to_ts = int(datetime.now(tz=timezone.utc).timestamp())
            from_ts = to_ts - 7*24*3600
            url = (f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from="
                   f"{datetime.utcfromtimestamp(from_ts).date()}&to={datetime.utcfromtimestamp(to_ts).date()}&token={FINNHUB_TOKEN}")
            j = requests.get(url, timeout=10).json()[:limit]
            for it in j:
                out.append({
                    "title": it.get("headline"),
                    "url": it.get("url"),
                    "summary": (it.get("summary") or "")[:180]
                })
        except Exception:
            pass
    return out

def fetch_analyst_score(ticker: str):
    score = None
    details = {}

    if FINNHUB_TOKEN:
        try:
            url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={FINNHUB_TOKEN}"
            j = requests.get(url, timeout=10).json()
            if isinstance(j, list) and j:
                latest = j[0]
                sb, b, h, s, ss = [latest.get(k, 0) for k in ("strongBuy","buy","hold","sell","strongSell")]
                total = sb + b + h + s + ss
                if total > 0:
                    score = round(((sb + 0.75*b + 0.5*h) / max(total,1))*100, 1)
                details = {"strongBuy": sb, "buy": b, "hold": h, "sell": s, "strongSell": ss}
        except Exception:
            pass

    if score is None:
        try:
            yq = Ticker(ticker)
            rt = yq.recommendation_trend
            if isinstance(rt, pd.DataFrame) and not rt.empty:
                row = rt.iloc[0]
                sb, b, h, s, ss = [int(row.get(k,0)) for k in ("strongBuy","buy","hold","sell","strongSell")]
                total = sb + b + h + s + ss
                if total>0:
                    score = round(((sb + 0.75*b + 0.5*h) / total)*100, 1)
                details = {"strongBuy": sb, "buy": b, "hold": h, "sell": s, "strongSell": ss}
        except Exception:
            pass

    return {"score": score, "breakdown": details}

def compute_composite_and_targets(ticker: str, ta_summary: dict, fundamentals: dict, analyst: dict):
    w_ta = 0.35
    w_fund = 0.30
    w_anl = 0.35

    ta_score = 50
    if ta_summary.get("trend") == "多頭":
        ta_score += 20
    elif ta_summary.get("trend") == "空頭":
        ta_score -= 20
    rsi = ta_summary.get("rsi14")
    if rsi is not None:
        if 45 <= rsi <= 60:
            ta_score += 10
        elif rsi < 30:
            ta_score -= 10
        elif rsi > 70:
            ta_score -= 5
    if ta_summary.get("close") and ta_summary.get("sma200"):
        if ta_summary["close"] > ta_summary["sma200"]:
            ta_score += 10
        else:
            ta_score -= 10
    ta_score = max(0, min(100, ta_score))

    fund_score = 50
    pe = fundamentals.get("pe")
    rg = fundamentals.get("rev_growth_yoy")
    if pe and pe>0:
        if pe < 15: fund_score += 15
        elif pe < 25: fund_score += 5
        else: fund_score -= 10
    if rg is not None:
        if rg > 10: fund_score += 15
        elif rg > 0: fund_score += 5
        else: fund_score -= 10
    fund_score = max(0, min(100, fund_score))

    anl_score = analyst.get("score") or 50

    composite = round(w_ta*ta_score + w_fund*fund_score + w_anl*anl_score, 1)

    close = ta_summary.get("close") or 0
    bb_mid = ta_summary.get("bb_mid") or close
    sma200 = ta_summary.get("sma200") or close

    if composite >= 65:
        action = "偏多（關注買入）"
        buy_zone = round(min(bb_mid, sma200) * 0.98, 2)
        tp = round(close * 1.08, 2)
        sl = round(close * 0.94, 2)
    elif composite <= 40:
        action = "偏空（關注賣出/減碼）"
        buy_zone = None
        tp = round(close * 0.94, 2)
        sl = round(close * 1.05, 2)
    else:
        action = "觀望（整理區間）"
        buy_zone = round(bb_mid, 2)
        tp = round(close * 1.04, 2)
        sl = round(close * 0.96, 2)

    return {
        "composite": composite,
        "action": action,
        "buy_zone": buy_zone,
        "take_profit": tp,
        "stop_loss": sl
    }

def build_report_text(ticker: str, ta_summary: dict, fundamentals: dict, analyst: dict, targets: dict, news_list: list):
    close = ta_summary.get("close")
    r = [
        f"【{ticker} 綜合分析】（台北時間 {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}）",
        "— 技術面 —",
        f"趨勢：{ta_summary.get('trend')} | 收盤：{close} | RSI14：{round(ta_summary.get('rsi14'),1) if ta_summary.get('rsi14') else 'NA'}",
        f"SMA50：{round(ta_summary.get('sma50'),2) if ta_summary.get('sma50') else 'NA'} | SMA200：{round(ta_summary.get('sma200'),2) if ta_summary.get('sma200') else 'NA'}",
        f"52W 區間：{round(ta_summary.get('range52')[0],2)} ~ {round(ta_summary.get('range52')[1],2)}" if ta_summary.get('range52') else "",
        "— 基本面 —",
        f"PE：{round(fundamentals.get('pe'),2) if fundamentals.get('pe') else 'NA'} | 市值：{fundamentals.get('mcap') if fundamentals.get('mcap') else 'NA'}",
        f"營收 YoY：{round(fundamentals.get('rev_growth_yoy'),1)}%" if fundamentals.get('rev_growth_yoy') is not None else "營收 YoY：NA",
        "— 機構評分 —",
        f"分數：{analyst.get('score') if analyst.get('score') is not None else 'NA'} / 100  明細：{analyst.get('breakdown')}",
        "— 綜合建議 —",
        f"Composite：{targets.get('composite')} / 100  ⇒ {targets.get('action')}",
        f"區間：買入參考 {targets.get('buy_zone')}｜TP {targets.get('take_profit')}｜SL {targets.get('stop_loss')}",
    ]

    if news_list:
        r.append("— 近期新聞 —")
        for i, n in enumerate(news_list, 1):
            r.append(f"{i}. {n.get('title','')}
   {n.get('url','')}")

    return "\n".join([x for x in r if x])

def run_full_analysis(ticker: str):
    px_df, ta_summary = fetch_price_and_ta(ticker)
    fundamentals = fetch_fundamentals(ticker)
    analyst = fetch_analyst_score(ticker)
    news_list = fetch_recent_news(ticker)
    targets = compute_composite_and_targets(ticker, ta_summary, fundamentals, analyst)

    report = build_report_text(ticker, ta_summary, fundamentals, analyst, targets, news_list)

    return {
        "ta": ta_summary,
        "fundamentals": fundamentals,
        "analyst": analyst,
        "targets": targets,
        "news": news_list,
        "report": report
    }
