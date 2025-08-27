# utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

# 建議使用台北時區，也可改成 UTC
scheduler = BackgroundScheduler(timezone="Asia/Taipei")

def _job_crawl_and_analyze():
    """
    排程工作：先抓社群，再跑分析。
    這裡採用「函式內延遲匯入」以避免循環匯入。
    """
    try:
        from utils.social_crawler import crawl_social_data
        crawl_social_data()
    except Exception as e:
        print("[scheduler] crawl_social_data failed:", e)

    try:
        from analyzer import analyze_data   # 若你的分析入口名稱不同，改這裡
        analyze_data()
    except Exception as e:
        print("[scheduler] analyze_data failed:", e)

# 每小時執行一次
try:
    scheduler.add_job(
        _job_crawl_and_analyze,
        "interval",
        hours=1,
        id="crawl_and_analyze",
        replace_existing=True,
        max_instances=1,  # 避免重疊
        coalesce=True     # 若有 miss 掉的觸發，合併執行一次
    )
except Exception as e:
    print("[scheduler] add_job error:", e)

def start():
    if not scheduler.running:
        scheduler.start()
        print("[scheduler] started")
