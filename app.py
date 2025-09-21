import os
from flask import Flask, request
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import Parser, MessageEvent, TextMessageContent
from analysis_pipeline import run_full_analysis

app = Flask(__name__)

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

handler = WebhookHandler(CHANNEL_SECRET)
api = MessagingApi(channel_access_token=CHANNEL_TOKEN)

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    events = Parser(signature, CHANNEL_SECRET).parse(body)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            text = (event.message.text or "").strip()
            if text.lower().startswith("/quote"):
                parts = text.split()
                if len(parts) >= 2:
                    ticker = parts[1].upper()
                    try:
                        res = run_full_analysis(ticker)
                        reply_text = res.get("report", "分析失敗，請稍後再試")
                    except Exception as e:
                        reply_text = f"發生錯誤：{e}"
                else:
                    reply_text = "用法：/quote <美股代碼>（例如 /quote AAPL）"
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text[:4900])]
                    )
                )
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
