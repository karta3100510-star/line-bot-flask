import yfinance as yf


def get_quote_summary(ticker):
try:
stock = yf.Ticker(ticker)
info = stock.info
price = info.get("regularMarketPrice")
pe = info.get("trailingPE")
change = info.get("regularMarketChangePercent")
low = info.get("fiftyTwoWeekLow")
high = info.get("fiftyTwoWeekHigh")
name = info.get("shortName")


return f"{name} ({ticker.upper()})\n現價: ${price} ({change:.2f}%)\n本益比: {pe}\n52週範圍: {low} - {high}"
except Exception as e:
return f"查詢錯誤: {e}"
