import os, json

DATA_FILE = os.path.join('data', 'posts.json')

def load_posts():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_posts(new_posts):
    posts = load_posts()
    posts.extend(new_posts)
    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)