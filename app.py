import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from utils.scheduler import scheduler
from analyzer import analyze_data
from utils.notifier import send_daily_summary
from utils.social_crawler import crawl_social_data
import config

app = Flask(__name__)
scheduler.start()

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    print("Request body:", body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    incoming = event.message.text.strip()

    if incoming.lower() == '/social':
        results = crawl_social_data()
        if not results:
            reply = "目前尚未抓取到任何社群內容。"
        else:
            lines = [f"{r['source']} → {r['data']}" for r in results]
            reply = "\n".join(lines[:10])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # Fallback: echo
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"You said: {incoming}"))

@app.route("/healthz", methods=['GET'])
def health_check():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

# === Enhanced command handlers ===
import re
from utils.social_crawler import crawl_social_data
from utils.analysis import fetch_quote, format_quote
from utils import summary as _summary
_TICKER_ONLY = re.compile(r"^[A-Za-z]{1,5}$")

def _format_social(max_items: int = 5):
    try:
        path = os.path.join("data", "social_posts.json")
        if not os.path.exists(path):
            return "目前沒有社群摘要。請先輸入 /crawl 抓取一次。"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return "目前沒有社群摘要。"
        rows = []
        for item in data[:max_items]:
            src = item.get("source","")
            tm = (item.get("time","") or "")[:19]
            tx = (item.get("text","") or "")[:80]
            url = item.get("url","")
            quotes = (item.get("analysis") or {}).get("quotes", [])
            qline = ""
            if quotes:
                q0 = quotes[0]
                # Build line defensively
                d1 = q0.get("chg_1d_pct"); m1 = q0.get("chg_1m_pct"); pe = q0.get("pe")
                d1s = "-" if d1 is None else f"{d1:.2f}%"
                m1s = "-" if m1 is None else f"{m1:.2f}%"
                pes = "-" if pe is None else f"{pe:.2f}"
                qline = f"\n↳ {q0.get('ticker','')} 1D {d1s} 1M {m1s} PE {pes}"
                if q0.get("recommend"):
                    qline += " ✅"
            rows.append(f"{src} | {tm}\n{tx}{(' ' + url) if url else ''}{qline}")
        return "\n\n".join(rows)[:1800]
    except Exception as e:
        return f"[讀取摘要失敗: {e}]"

def _handle_text_command(text: str):
    t = text.strip()
    low = t.lower()
    if low == "/social":
        return _format_social(5)
    if low == "/crawl":
        items = crawl_social_data()
        n = len(items) if isinstance(items, list) else 0
        return f"已重新抓取社群內容，共 {n} 則。\n\n" + _format_social(5)
    if low == "/summary":
        return _summary.daily_summary_text()
    if low in ("/help", "help"):
        return "指令：\n/social 查看最新社群摘要\n/crawl 立即抓取一次\n/summary 每日盤後摘要\n<股票代碼> 例如 NVDA、PLTR"
    if _TICKER_ONLY.match(t):
        q = fetch_quote(t.upper())
        return format_quote(q)
    return "我在這裡～ 輸入 /help 看可用指令。"
