from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json
from utils.analyzer import ensure_analysis_file

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    if text == "/healthz":
        reply = "Bot is running."
    elif text == "/summary":
        try:
            with open("data/analysis.json", "r") as f:
                data = json.load(f)
            reply = json.dumps(data[-1], ensure_ascii=False, indent=2) if data else "目前尚無任何分析結果。"
        except Exception as e:
            reply = f"讀取分析資料時發生錯誤: {e}"
    else:
        reply = f"You said: {text}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok"

if __name__ == "__main__":
    ensure_analysis_file()
    app.run(host="0.0.0.0", port=8080)
