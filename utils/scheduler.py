# utils/scheduler.py  (shim)
# 轉接到 scheduler_fix，避免在 import 當下就呼叫 analyze_data。
from .scheduler_fix import scheduler, start, diagnostics  # re-export
# 不做任何 add_job 操作，所有排程註冊/啟動交給 scheduler_fix.start()
