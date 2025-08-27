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
