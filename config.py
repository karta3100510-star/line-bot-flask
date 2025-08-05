# config.py
import os
from dotenv import load_dotenv

# 本地開發時載入 .env，部署時由環境變數提供
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET      = os.getenv("LINE_CHANNEL_SECRET")
USER_ID                  = os.getenv("USER_ID")
