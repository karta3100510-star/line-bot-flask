import os, json

def send_daily_summary():
    try:
        with open(os.path.join('data', 'analysis.json'), 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("No analysis data available.")
        return

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