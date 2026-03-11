import json
import math
from collections import defaultdict

# Ajusta si tu classid de ball fuera distinto
BALL = 0
REF = 3

with open("outputs/records_paula.json", "r", encoding="utf-8") as f:
    records = json.load(f)

frames = defaultdict(list)
for r in records:
    frames[r["frameid"]].append(r)

def center(b):
    x1, y1, x2, y2 = b
    return ((x1 + x2) / 2, (y1 + y2) / 2)

dists = []

for fid, rs in frames.items():
    balls = [r for r in rs if r.get("classid") == BALL]
    if not balls:
        continue

    ball_c = center(balls[0]["bbox"])

    players = [
        r for r in rs
        if r.get("classname") in ("player", "goalkeeper")
        and r.get("classid") != REF
    ]

    if not players:
        continue

    best = min(
        math.hypot(
            center(p["bbox"])[0] - ball_c[0],
            center(p["bbox"])[1] - ball_c[1],
        )
        for p in players
    )

    dists.append(best)

print("Frames with ball+players:", len(dists))

if dists:
    dists_sorted = sorted(dists)

    def pct(p):
        idx = int(p * len(dists_sorted)) - 1
        idx = max(0, min(idx, len(dists_sorted) - 1))
        return dists_sorted[idx]

    print("Min:", dists_sorted[0])
    print("P25:", pct(0.25))
    print("P50:", pct(0.50))
    print("P75:", pct(0.75))
    print("P90:", pct(0.90))
    print("Max:", dists_sorted[-1])
else:
    print("No overlapping frames found.")