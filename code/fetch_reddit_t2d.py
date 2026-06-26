import requests
import json
import time

THREAD_URLS = [
    "https://www.reddit.com/r/diabetes/comments/16106zx/most_people_do_this_after_their_diagnosis_with/",
    "https://www.reddit.com/r/diabetes/comments/1nmtds5/recently_diagnosed_type_2devastated/",
    "https://www.reddit.com/r/diabetes/comments/1awru2n/anyone_successfully_reversed_type_2/",
    "https://www.reddit.com/r/diabetes/comments/1aldlbz/i_had_undiagnosed_type_2_diabetes_for_6_years/",
    "https://www.reddit.com/r/diabetes/comments/1mdpdx8/would_taking_insulin_as_a_type_2_diabetic_be_bad/",
    "https://www.reddit.com/r/diabetes/comments/1231eao/life_expectancy_with_type_2_diagnosed_at_age_25/",
    "https://www.reddit.com/r/diabetes/comments/1b95v8a/shame_and_regret_over_being_diagnosed_with_type_2/",
    "https://www.reddit.com/r/diabetes/comments/1lod3lp/for_those_who_developed_type_2_through_lifestyle/",
    "https://www.reddit.com/r/diabetes/comments/1204ilm/can_you_really_reverse_type_2_diabetes/",
    "https://www.reddit.com/r/diabetes/comments/1irzf4/i_feel_guilty_and_ashamed_of_being_a_young_type_2/",
    "https://www.reddit.com/r/diabetes/comments/1die73f/i_didnt_know_type_2_was_permanent_why/",
    "https://www.reddit.com/r/diabetes/comments/18s1zss/my_dad_got_diagnosed_with_type_2_diabetes_is_it_a/",
    "https://www.reddit.com/r/diabetes/comments/1guz1ge/what_really_causes_type_2_diabetes/",
    "https://www.reddit.com/r/diabetes/comments/1fnfa55/diabetes_at_young_age_and_longevity/",
    "https://www.reddit.com/r/diabetes/comments/1k7g0kr/how_bad_is_type_2_diabetes_if_i_end_up_getting_it/",
    "https://www.reddit.com/r/diabetes/comments/1mi9haq/why_are_type2_stigmatized_and_blamed_for_their/",
    "https://www.reddit.com/r/diabetes/comments/m6iq5q/im_26_and_diagnosed_with_type2_diabetes_if_i_take/",
    "https://www.reddit.com/r/diabetes/comments/1n1qhpu/dont_relapse_if_your_type_2/",
    "https://www.reddit.com/r/diabetes/comments/1ip6dp1/type_2_diabetic_who_used_to_struggle_maybe_my/",
    "https://www.reddit.com/r/diabetes/comments/pty3il/redditors_with_type_2_diabetes_what_were_your/",
    "https://www.reddit.com/r/diabetes/comments/1hqdklu/type_2_diabetes_isnt_as_bad_as_is/",
    "https://www.reddit.com/r/diabetes/comments/1m3iu47/the_mental_load_of_type_2_diabetes/",
    "https://www.reddit.com/r/diabetes/comments/1mkeju3/i_just_got_diagnosed_with_type_2_diabetes_and_i/",
    "https://www.reddit.com/r/diabetes/comments/1ovl3v2/just_diagnosed_with_type_2_diabetes_today_my_bday/",
    "https://www.reddit.com/r/diabetes/comments/1fqz74m/whos_the_oldest_person_you_know_who_has_type_2/",
    "https://www.reddit.com/r/diabetes/comments/m4xjr1/type_2_diabetes_can_you_have_type_2_diabetes/",
    "https://www.reddit.com/r/diabetes/comments/118ddgm/type_2_diabetic_for_twenty_years/",
    "https://www.reddit.com/r/diabetes/comments/qd8lwn/am_i_stupid_for_crying_about_having_type_2/",
    "https://www.reddit.com/r/diabetes/comments/1l6hndw/newly_diagnosed_with_type_2_one_month_update/",
    "https://www.reddit.com/r/diabetes/comments/1lq3pk4/just_diagnosed_with_type_2_diabetes_completely_in/",
    "https://www.reddit.com/r/diabetes/comments/1hb69ft/what_are_odds_of_type_2_diabetes_if_my_dad_has_it/"
]

def get_thread_id(url: str) -> str:
    parts = url.split("/")
    for i, p in enumerate(parts):
        if p == "comments" and i + 1 < len(parts):
            return parts[i + 1]   # the thing right after "comments" is the ID
    raise ValueError(f"Could not find thread id in URL: {url}")


def fetch_thread_json(thread_id):
    api_url = f"https://www.reddit.com/comments/{thread_id}.json"
    headers = {"User-Agent": "Mozilla/5.0 (TrustMed Bot)"}
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    import os
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "t2d_reddit_threads.jsonl")
    with open(output_path, "w", encoding="utf-8") as fout:
        for url in THREAD_URLS:
            thread_id = get_thread_id(url)
            print(f"Fetching {thread_id} ...")
            try:
                data = fetch_thread_json(thread_id)
            except Exception as e:
                print(f"Failed: {thread_id} → {e}")
                continue

            # Extract OP
            op = data[0]["data"]["children"][0]["data"]
            op_text = op.get("selftext", "").strip()
            if op_text:
                op_rec = {
                    "thread_id": thread_id,
                    "source": "reddit_r_diabetes",
                    "thread_url": url,
                    "post_id": f"{thread_id}_op",
                    "role": "OP",
                    "text": op_text
                }
                fout.write(json.dumps(op_rec) + "\n")

            # Extract top-level replies
            comments = data[1]["data"]["children"]
            for i, c in enumerate(comments, start=1):
                if c["kind"] != "t1":  
                    continue
                body = c["data"].get("body", "").strip()
                if not body:
                    continue
                reply_rec = {
                    "thread_id": thread_id,
                    "source": "reddit_r_diabetes",
                    "thread_url": url,
                    "post_id": f"{thread_id}_c{i}",
                    "role": "reply",
                    "text": body
                }
                fout.write(json.dumps(reply_rec) + "\n")

            time.sleep(1)  # avoid rate limits

    print(f"DONE! Saved to {output_path}")

if __name__ == "__main__":
    main()
