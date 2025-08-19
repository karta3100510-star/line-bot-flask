import json
def send_daily_summary():
    try:
        with open("data/analysis.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print("推播社群摘要：", data)
    except Exception as e:
        print("錯誤：無法載入分析結果", e)
