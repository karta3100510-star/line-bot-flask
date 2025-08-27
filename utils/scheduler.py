from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="Asia/Taipei")

def _job_crawl_and_analyze():
    # 1) 先爬社群
    try:
        from utils.social_crawler import crawl_social_data
        crawl_social_data()
    except Exception as e:
        print("[scheduler] crawl_social_data failed:", e)

    # 2) 再做分析（延遲匯入，避免循環）
    analyze_data = None
    try:
        from analyzer import analyze_data as _an
        analyze_data = _an
    except Exception:
        try:
            from analyzer_core import analyze_data as _an
            analyze_data = _an
        except Exception as e:
            print("[scheduler] cannot import analyze_data:", e)
            return

    try:
        analyze_data()
    except Exception as e:
        print("[scheduler] analyze_data failed:", e)

# 每小時跑一次（以函式為目標，安全）
try:
    scheduler.add_job(
        _job_crawl_and_analyze,
        "interval",
        hours=1,
        id="crawl_and_analyze",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
except Exception as e:
    print("[scheduler] add_job error:", e)

def start():
    if not scheduler.running:
        scheduler.start()
        print("[scheduler] started")
