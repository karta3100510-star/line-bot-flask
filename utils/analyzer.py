import os
import json

def load_analysis():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists("data/analysis.json"):
        with open("data/analysis.json", "w") as f:
            json.dump([], f)
    with open("data/analysis.json", "r") as f:
        return json.load(f)

def save_analysis(data):
    os.makedirs("data", exist_ok=True)
    with open("data/analysis.json", "w") as f:
        json.dump(data, f, indent=2)
