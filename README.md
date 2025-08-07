# 股票追踪与筛选工具 (v6)

## 功能概览
- 移除 dotenv 依赖，使用环境变量便捷读取
- 每小时抓取并分析社群来源 (共 8 条链接)
- 自动加入超过2次转发来源
- 抽取帖子中的可能股票代号
- 分析近1个月价格变动、P/E、机构推荐评级
- 自动筛选：抗跌 (跌幅 <5%)、估值偏低 (P/E <15)、评级 <3
- 每日中午 12:00 推播推荐结果
- 部署配置：Procfile, runtime.txt

## 安装与运行
1. 安装依赖: `pip install -r requirements.txt`
2. 在 Render 或其他平台的 Dashboard 设置环境变量:
   - LINE_CHANNEL_SECRET
   - LINE_CHANNEL_ACCESS_TOKEN
3. 运行: `gunicorn app:app`

## 目录结构
```
.
├── app.py
├── config.py
├── analyzer.py
├── Procfile
├── README.md
├── requirements.txt
├── runtime.txt
├── data
│   ├── analysis.json
│   └── posts.json
└── utils
    ├── notifier.py
    ├── scheduler.py
    ├── social_crawler.py
    └── storage.py
```
