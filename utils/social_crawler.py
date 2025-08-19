def crawl_social_data():
    print("模擬抓取社群資料...（之後可改為 Graph API）")
    with open("data/analysis.json", "w", encoding="utf-8") as f:
        f.write('{"mock": true}')
