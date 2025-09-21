# LINE Bot 一鍵分析（技術 + 基本面 + 新聞 + 機構評分）

用法：在 LINE 私聊或群組輸入
```
/quote <TICKER>
```
例如：`/quote AAPL`

## 功能
- 技術面：SMA20/50/200、MACD、RSI、布林帶、52W 範圍、自動判斷趨勢
- 基本面：PE、市值、營收 YoY（近幾期估算）
- 新聞：AlphaVantage 或 Finnhub 近 7 天新聞摘要
- 機構評分：Finnhub 或 Yahoo 的 recommendation trend 轉換為 0~100 分
- 綜合建議：技術+基本面+機構評分 加權計算出 Composite 分數，並給出買入參考/TP/SL

## 部署
### 1) 本機/開發
```bash
pip install -r requirements.txt
export LINE_CHANNEL_SECRET=...
export LINE_CHANNEL_ACCESS_TOKEN=...
# 選填其中之一（或兩者都填）
export FINNHUB_TOKEN=...
export ALPHAVANTAGE_KEY=...
python app.py
```
設定反向代理（如 ngrok）將 `https://<your-public-url>/callback` 綁到 LINE webhook。

### 2) Render
- 直接匯入此專案（或自行上傳到 GitHub 再 Import）
- 確認 `render.yaml` 建立 Web Service
- 設定環境變數（LINE/Finnhub/AlphaVantage）
- Health check path: `/healthz`
- Start command: `python -m gunicorn app:app`

## 常見問題
- 若 `pandas_ta` 安裝慢：Render 會自動快取，之後較快
- Yahoo 資料偶爾失敗：稍後重試或改用 FinanceToolkit/FMP
- 回覆過長：程式已將文字裁切至 ~4900 字（LINE 限制）

## 目錄
- `app.py`：Flask + LINE webhook，處理 `/quote`
- `analysis_pipeline.py`：抓行情/指標、基本面、新聞、機構評分、綜合建議
- `requirements.txt`、`Procfile`、`runtime.txt`、`render.yaml`
- `.env.example`
