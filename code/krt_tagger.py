import json
import os

# Path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_krt_patterns(path=None):
    if path is None:
        path = os.path.join(DATA_DIR, "krt_patterns.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_krt_in_text(text, patterns):
    text_l = text.lower()
    hits = []
    for krt_id, rule in patterns.items():
        must = [w.lower() for w in rule.get("must_contain_any", [])]
        also = [w.lower() for w in rule.get("also_contain_any", [])]
        if must and not any(w in text_l for w in must):
            continue
        if also and not any(w in text_l for w in also):
            continue
        hits.append(krt_id)
    return hits

def tag_posts(
    posts_path=None,
    out_path=None,
    patterns_path=None,
):
    if posts_path is None:
        posts_path = os.path.join(DATA_DIR, "t2d_reddit_threads.jsonl")
    if out_path is None:
        out_path = os.path.join(DATA_DIR, "t2d_reddit_threads_tagged.jsonl")
    if patterns_path is None:
        patterns_path = os.path.join(DATA_DIR, "krt_patterns.json")
    patterns = load_krt_patterns(patterns_path)
    total = 0
    with open(posts_path, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            total += 1
            post = json.loads(line)
            text = post.get("text", "")
            krt_hits = detect_krt_in_text(text, patterns)
            post["krt_ids"] = krt_hits
            fout.write(json.dumps(post, ensure_ascii=False) + "\n")
    print(f"Tagged {total} posts and wrote to {out_path}")

if __name__ == "__main__":
    tag_posts()
