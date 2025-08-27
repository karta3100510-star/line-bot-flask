import os
import json
import traceback
import re
from flask import Flask, request, abort, jsonify

# ===== Flask =====
app = Flask(__name__)

# ===== LINE SDK =====
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

_line_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) if LINE_CHANNEL_ACCESS_TOKEN else None
_parser = WebhookParser(LINE_CHANNEL_SECRET) if LINE_CHANNEL_SECRET else None

# ===== Health Check =====
@app.get("/healthz")
def healthz():
    return jsonify({"ok": True}), 200

# ===== APScheduler start (safe) =====
# Import only the 'start' function to avoid circular imports and premature job wiring.
try:
    from utils.scheduler import start as start_scheduler
    try:
        start_scheduler()
        print("[scheduler] started")
    except Exception as e:
        print("[scheduler] start error:", e)
except Exception as e:
    print("[scheduler] not configured:", e)

# ===== Helpers =====
def _reply_text(reply_token: str, text: str):
    try:
        if _line_api:
            _line_api.reply_message(reply_token, TextSendMessage(text=text))
        else:
            print("[debug reply]", text)
    except LineBotApiError as e:
        print("[LineBotApiError]", e)

def _fmt_num(x, suf=""):
    return "-" if x is None else (f"{x:.2f}{suf}" if isinstance(x,(int,float)) else str(x))

def _format_items(items, max_items: int = 5):
    if not items: 
        return "目前沒有社群摘要。"
    rows = []
    for item in items[:max_items]:
        src = item.get("source","")
        tm = (item.get("time","") or "")[:19]
        tx = (item.get("text","") or "")[:80]
        url = item.get("url","")
        quotes = (item.get("analysis") or {}).get("quotes", []) if isinstance(item.get("analysis"), dict) else []
        qline = ""
        if quotes:
            q0 = quotes[0]
            d1 = q0.get("chg_1d_pct"); m1 = q0.get("chg_1m_pct"); pe = q0.get("pe")
            qline = f"\n↳ {q0.get('ticker','')} 1D {_fmt_num(d1,'%')} 1M {_fmt_num(m1,'%')} PE {_fmt_num(pe)}"
            if q0.get("recommend"):
                qline += " ✅"
        rows.append(f"{src} | {tm}\n{tx}{(' ' + url) if url else ''}{qline}")
    return "\n\n".join(rows)[:1800]

def _format_social_from_file(max_items: int = 5):
    try:
        path = os.path.join("data", "social_posts.json")
        if not os.path.exists(path):
            return "目前沒有社群摘要。請先輸入 /crawl 抓取一次。"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return "目前沒有社群摘要。"
        return _format_items(data, max_items)
    except Exception as e:
        return f"[讀取摘要失敗: {e}]"

_TICKER_ONLY = re.compile(r"^[A-Za-z]{1,5}$")

def _handle_text_command(text: str) -> str:
    t = (text or "").strip()
    low = t.lower()

    if low == "/social":
        return _format_social_from_file(5)

    if low == "/crawl":
        # Lazy import to avoid cycles at startup
        try:
            from utils.social_crawler import crawl_social_data
            items = crawl_social_data()
            n = len(items) if isinstance(items, list) else 0
            # 直接用回傳結果渲染，避免某些版本沒有寫入檔案
            return f"已重新抓取社群內容，共 {n} 則。\n\n" + _format_items(items, 5)
        except Exception as e:
            return f"[抓取失敗] {e}"

    if low == "/summary":
        try:
            from utils import summary as _summary
            return _summary.daily_summary_text()
        except Exception as e:
            return f"[摘要模組不可用] {e}\n提示：請確認 utils/summary.py 是否存在。"

    if low in ("/help","help"):
        return "指令：\n/social 查看最新社群摘要\n/crawl 立即抓取一次\n/summary 每日盤後摘要\n<股票代碼> 例如 NVDA、PLTR"

    # Ticker lookup
    if _TICKER_ONLY.match(t):
        try:
            from utils.analysis import fetch_quote
            # 嘗試載入 format_quote（若不存在不報錯）
            try:
                from utils.analysis import format_quote as _format_quote
            except Exception:
                _format_quote = None
            q = fetch_quote(t.upper())
            if callable(_format_quote):
                return _format_quote(q)  # type: ignore
            # Fallback quick format
            return f"{q.get('ticker','')} | ${_fmt_num(q.get('price'))} | 1D {_fmt_num(q.get('chg_1d_pct'),' %')} | 1M {_fmt_num(q.get('chg_1m_pct'),' %')} | PE {_fmt_num(q.get('pe'))}"
        except Exception as e:
            return f"[查價失敗] {e}"

    return "我在這裡～ 輸入 /help 看可用指令。"

# ===== LINE Webhook =====
@app.post("/callback")
def callback():
    sig = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    # Basic logs for debugging on Render
    print("[/callback] signature:", sig)
    print("[/callback] body:", body[:500])

    if not _parser:
        print("[warn] LINE secrets not configured.")
        return "ok", 200

    try:
        events = _parser.parse(body, sig)
    except InvalidSignatureError:
        print("[error] InvalidSignatureError")
        abort(400)

    for ev in events:
        try:
            if isinstance(ev, MessageEvent) and isinstance(ev.message, TextMessage):
                msg = _handle_text_command(ev.message.text)
                _reply_text(ev.reply_token, msg)
        except Exception as e:
            print("[handler error]", e)
            print(traceback.format_exc())
            _reply_text(ev.reply_token, f"[發生錯誤] {e}")

    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
