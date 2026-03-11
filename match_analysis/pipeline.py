# match_analysis/pipeline.py

import json
import os
from collections import defaultdict
from typing import List, Dict, Any

from .jersey_clustering import collect_jersey_samples, assign_teams_track_pixels
from .possession import compute_possession
from .annotate import annotate_records


def run_pipeline(
    input_path: str,
    output_path: str = "outputs/tracks_annotated.json",
) -> List[Dict[str, Any]]:
    """
    End-to-end team assignment and ball possession pipeline. [file:46]
    """
    with open(input_path, "r") as f:
        records: List[Dict[str, Any]] = json.load(f)

    print("=" * 56)
    print("Team Assignment & Ball Possession")
    print("=" * 56)

    frames = {r["frameid"] for r in records}
    dist = defaultdict(int)
    for r in records:
        dist[r["classname"]] += 1

    print(f"[1] Using {len(records)} pre-built records across {len(frames)} frames")
    for cls, n in sorted(dist.items()):
        if cls in ("player", "goalkeeper"):
            tag = "[P]"
        elif cls == "ball":
            tag = "[B]"
        else:
            tag = "[S]"
        print(f"  {tag} {cls:10s} {n}")

    print("[2] Extracting jersey pixels")
    track_pixels = collect_jersey_samples(records)
    print(f"    Pixel arrays for {len(track_pixels)} player tracks")

    print("[3] Clustering jerseys – team IDs")
    team_ids, team_colors = assign_teams_track_pixels(track_pixels)
    for team in (0, 1):
        members = [t for t, v in team_ids.items() if v == team]
        if members:
            c = team_colors[members[0]]
            print(f"  Team {team} {len(members)} tracks, colour RGB{c}")

    print("[4] Computing ball possession")
    frame_possession, running_stats = compute_possession(records, team_ids)
    if running_stats:
        final = list(running_stats.values())[-1]
        t0 = final.get("team0pct", 0)
        t1 = final.get("team1pct", 0)
        none_pct = round(100.0 - t0 - t1, 1)
        print(f"  Team 0 {t0:.1f} Team 1 {t1:.1f} None {none_pct:.1f}")

    annotated = annotate_records(
        records,
        team_ids,
        team_colors,
        frame_possession,
        running_stats,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(annotated, f, indent=2)
    print(f"Saved {len(annotated)} annotated records {output_path}")

    return annotated

