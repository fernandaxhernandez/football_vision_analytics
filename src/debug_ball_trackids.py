import json
from collections import Counter

rec = json.load(open("outputs/records_paula.json", "r", encoding="utf-8"))

ball_trackids = Counter()

for r in rec:
    if r["classname"] == "ball":
        ball_trackids[r["trackid"]] += 1

print("Ball track IDs distribution:")
print(ball_trackids)