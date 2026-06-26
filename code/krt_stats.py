import json
import os
import collections
import itertools

# Path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
IN_PATH = os.path.join(DATA_DIR, "t2d_reddit_threads_tagged.jsonl")

def main():
    total_posts = 0
    posts_with_any = 0
    krt_counts = collections.Counter()
    co_counts = collections.Counter()

    with open(IN_PATH, "r", encoding="utf-8") as f:
        for line in f:
            total_posts += 1
            obj = json.loads(line)
            ks = obj.get("krt_ids", [])
            if ks:
                posts_with_any += 1
            for k in ks:
                krt_counts[k] += 1
            for a, b in itertools.combinations(sorted(set(ks)), 2):
                co_counts[(a, b)] += 1

    print(f"Total posts: {total_posts}")
    print(f"Posts with ≥1 KRT: {posts_with_any} "
          f"({posts_with_any/total_posts*100:.1f}%)\n")

    print("Per-KRT counts:")
    for k, c in krt_counts.most_common():
        pct = c / total_posts * 100
        print(f"  {k}: {c} posts ({pct:.1f}%)")

    print("\nTop KRT co-occurrences:")
    for (a, b), c in co_counts.most_common(10):
        print(f"  {a} + {b}: {c} posts")

if __name__ == "__main__":
    main()
