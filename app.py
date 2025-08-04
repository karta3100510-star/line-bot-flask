from flask import Flask, request, abort
from linebot import LineBotSdk
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    WebhookHandler,
    MessageEvent,
    TextMessageContent
)
import os

# 初始化 Flask
app = Flask(__name__)

# LINE BOT Token 與 Secret
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的長效金鑰")
channel_secret = os.getenv("LINE_CHANNEL_SECRET", "你的 channel secret")

# 初始化 LINE API
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# 回覆訊息功能
def reply_text(reply_token, text):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )

# 接收 webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)
    return "OK"

# 處理訊息事件
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    msg = event.message.text.strip().lower()

    if msg == "/test":
        reply_text(event.reply_token, "✅ 連線成功")
    elif msg == "/start":
        reply_text(event.reply_token, "請輸入美股代碼或輸入：市場摘要、佩羅西、便宜股")
    elif msg in ["市場摘要"]:
        reply_text(event.reply_token, "📊 市場摘要功能建構中，敬請期待")
    elif msg in ["佩羅西"]:
        reply_text(event.reply_token, "🔍 分析中：佩羅西目前持有與買進標的建構中")
    elif msg.isalpha() and len(msg) <= 5:
        reply_text(event.reply_token, f"你輸入的是：{msg.upper()}（稍後將顯示即時股價與簡析）")
    else:
        reply_text(event.reply_token, f"你說的是：{event.message.text}")

# Health check endpoint for Render
@app.route("/healthz")
def health_check():
    return "ok", 200

# 主程式入口
if __name__ == "__main__":
    app.run(debug=True)


