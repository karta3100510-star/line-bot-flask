# utils/subscriber.py
import os, json

DATA_FILE = os.path.join('data', 'subscribers.json')

def load_subscribers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def add_subscriber(user_id):
    subs = load_subscribers()
    if user_id not in subs:
        subs.append(user_id)
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(subs, f, ensure_ascii=False, indent=2)
