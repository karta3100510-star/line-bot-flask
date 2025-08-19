import os, json
from linebot import LineBotApi
from linebot.models import TextSendMessage
import config

def load_subscribers():
    return ["你自己的 LINE userId"]  # 測試用

def send_daily_summary():
    try:
        with open(os.path.join('data', 'analysis.json'), 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("No analysis data available.")
        return

    recommended = [r for r in results if r.get('recommend')]
    if not recommended:
        message = "今日無推薦標的。"
    else:
        lines = [f"{r['ticker']}: 1月變動 {r['change_1mo']:.2f}%, P/E={r['pe']}, 建議 買入" for r in recommended]
        message = "\n".join(lines)

    bot = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
    for uid in load_subscribers():
        try:
            bot.push_message(uid, TextSendMessage(text=message))
        except Exception as e:
            print(f"推播失敗: {e}")
