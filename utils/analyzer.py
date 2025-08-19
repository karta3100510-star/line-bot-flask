import os
import json

def ensure_analysis_file():
    os.makedirs("data", exist_ok=True)
    path = "data/analysis.json"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
