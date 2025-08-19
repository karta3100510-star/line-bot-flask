import os, json
def load_posts():
    if not os.path.exists("data/posts.json"): return []
    with open("data/posts.json", "r") as f: return json.load(f)

def save_posts(new_data):
    posts = load_posts()
    posts.extend(new_data)
    with open("data/posts.json", "w") as f: json.dump(posts, f, ensure_ascii=False, indent=2)
