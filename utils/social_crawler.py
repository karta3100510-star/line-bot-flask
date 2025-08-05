# utils/social_crawler.py
import requests

def fetch_social_metrics():
    """
    範例：抓取 Telegram 頻道成員數 (請自行替換 Bot Token 與 chat_id)
    """
    BOT_TOKEN = "<YOUR_TELEGRAM_BOT_TOKEN>"
    CHAT_ID   = "@YourChannelName"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMembersCount?chat_id={CHAT_ID}"
    r   = requests.get(url)
    j   = r.json()
    return {"telegram_count": j.get("result")}
