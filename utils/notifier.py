import os, json
from linebot import LineBotApi
 from linebot.models import TextSendMessage
import config
from utils.subscriber import load_subscribers

def send_daily_summary():
    # 载入分析结果
     try:
         with open(os.path.join('data', 'analysis.json'), 'r') as f:
             results = json.load(f)
             except FileNotFoundError:
                  print("No analysis data available.")
                 return
# 构建消息文本
recommended = [r for r in results if r.get('recommend')]
if not recommended:
    message = "今日無推薦標的。"
else:
lines = []
for r in recommended:
    lines.append(f"{r['ticker']}: 1月變動 {r['change_1mo']:.2f}%, P/E={r['pe']} 建議買入")
 message = "\n".join(lines)

 # 推送给所有订阅者
bot = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
subs = load_subscribers()
for uid in subs:
    try:
        bot.push_message(uid, TextSendMessage(text=message))
        except Exception as e:
            print(f"Failed to push to {uid}: {e}")

    recommended = [r for r in results if r.get('recommend')]
    if not recommended:
        message = "今日無推薦標的。"
    else:
        lines = []
        for r in recommended:
            lines.append(f"{r['ticker']}: 1月變動 {r['change_1mo']:.2f}%, P/E={r['pe']}, 建議 買入")
        message = "\n".join(lines)

    # Placeholder: integrate LINE API push here
    print("每日總結：")
    print(message)
