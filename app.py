from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

import os

app = Flask(__name__)

# LINE credentials from environment
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running."

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()

    # /test 指令確認連線
    if user_msg.lower() == "/test":
        reply = "✅ 已連線成功：/test"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # /start 快速回覆按鈕
    if user_msg.lower() == "/start":
        reply = TextSendMessage(
            text="請選擇功能：",
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="市場摘要", text="市場摘要")),
                QuickReplyButton(action=MessageAction(label="佩羅西", text="佩羅西")),
                QuickReplyButton(action=MessageAction(label="便宜股推薦", text="便宜股推薦")),
                QuickReplyButton(action=MessageAction(label="查詢個股", text="Pltr"))
            ])
        )
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # 市場摘要
    if "市場摘要" in user_msg:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📰 今日市場摘要建構中..."))
        return

    # 關鍵字自動回覆
    if "佩羅西" in user_msg:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="👩‍🦳 佩羅西持股建構中..."))
        return

    # 股票代碼 echo
    if user_msg.lower() in ["pltr", "nvda", "aapl", "tsla", "msft"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"你說的是：{user_msg}"))
        return

    # 預設回覆
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"你說的是：{user_msg}"))

if __name__ == "__main__":
    app.run()


