# match_analysis/possession.py

import math
from collections import defaultdict
from typing import Dict, List, Tuple, Any

from .config import POSSESSION_THRESHOLD, REFEREE_CLASS_ID, BALL_CLASS_ID  # [file:46]


def bbox_center(bbox):
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def euclidean(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def compute_possession(
    records: List[Dict[str, Any]],
    team_ids: Dict[int, int],
) -> Tuple[Dict[int, int | None], Dict[int, Dict[str, float | int]]]:
    """
    Ball-possession assignment per frame, using a distance threshold. [file:46]

    Returns:
      frame_possession: frameid -> trackid or None
      running_stats: frameid -> {
         team0pct, team1pct, team0frames,
         team1frames, noneframes, totalframes
      }
    """
    by_frame: Dict[int, Dict[int, Dict[str, Any]]] = defaultdict(dict)
    for rec in records:
        by_frame[rec["frameid"]][rec["trackid"]] = rec

    frame_possession: Dict[int, int | None] = {}
    counts = {"team0": 0, "team1": 0, "none": 0}
    running_stats: Dict[int, Dict[str, float | int]] = {}

    for fid in sorted(by_frame.keys()):
        frame = by_frame[fid]
        ball = frame.get(BALL_CLASS_ID, None)

        if ball is None:
            frame_possession[fid] = None
            counts["none"] += 1
        else:
            ball_c = bbox_center(ball["bbox"])
            best_tid, best_d = None, float("inf")

            for tid, rec in frame.items():
                if tid == BALL_CLASS_ID or rec.get("classid") == REFEREE_CLASS_ID:
                    continue
                d = euclidean(bbox_center(rec["bbox"]), ball_c)
                if d < best_d:
                    best_d, best_tid = d, tid

            if best_tid is not None and best_d <= POSSESSION_THRESHOLD:
                frame_possession[fid] = best_tid
                t = team_ids.get(best_tid, None)
                if t == 0:
                    counts["team0"] += 1
                elif t == 1:
                    counts["team1"] += 1
                else:
                    counts["none"] += 1
            else:
                frame_possession[fid] = None
                counts["none"] += 1

        total = counts["team0"] + counts["team1"] + counts["none"]
        if total == 0:
            running_stats[fid] = {
                "team0pct": 0.0,
                "team1pct": 0.0,
                "team0frames": counts["team0"],
                "team1frames": counts["team1"],
                "noneframes": counts["none"],
                "totalframes": total,
            }
        else:
            running_stats[fid] = {
                "team0pct": round(counts["team0"] / total * 100, 1),
                "team1pct": round(counts["team1"] / total * 100, 1),
                "team0frames": counts["team0"],
                "team1frames": counts["team1"],
                "noneframes": counts["none"],
                "totalframes": total,
            }

    return frame_possession, running_stats

