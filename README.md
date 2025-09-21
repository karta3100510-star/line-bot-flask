# LINE Bot 一鍵分析（含 Scheduler 熱修復）

## 指令
- `/quote <TICKER>`：回覆技術＋基本面＋新聞＋機構評分＋建議價位
- `GET /healthz`：健康檢查
- `GET /debug`：顯示正在使用的 scheduler 模組與版本

## 部署（Render）
1. 設定環境變數：LINE_CHANNEL_SECRET、LINE_CHANNEL_ACCESS_TOKEN（必要）；FINNHUB_TOKEN/ALPHAVANTAGE_KEY（二擇一或都填）
2. Deploy：使用此專案的 `render.yaml`，Start Command 為 `python -m gunicorn app:app`。
3. Webhook：在 LINE Developers 將 `https://<your-domain>/callback` 設為 Webhook URL。

## 說明
- 我們提供 `utils/scheduler_fix.py`，避免舊版 `utils/scheduler.py` 在 import 時就調用未定義的 `analyze_data` 導致崩潰的問題。
- `analyzer.py`、`utils/notifier.py` 也提供最小可運行版本，後續可替換為你的真實邏輯。
