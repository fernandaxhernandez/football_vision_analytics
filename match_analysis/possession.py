# match_analysis/possession.py
from __future__ import annotations

import math
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional

from .config import POSSESSION_THRESHOLD, BALL_CLASS_ID, REFEREE_CLASS_ID

def bbox_center(bbox: List[float]) -> Tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def euclidean(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def compute_possession(
    records: List[Dict[str, Any]],
    team_ids: Dict[int, int],
) -> Tuple[Dict[int, Optional[int]], Dict[int, Dict[str, float]]]:
    """
    Compute, per frame, which team has possession.

    Args:
      records: list of records, each with keys: frameid, classname, classid, trackid, bbox, conf, imagepath...
      team_ids: mapping from trackid -> team_id (0 or 1)

    Returns:
      frame_possession: dict[frameid] -> team_id or None
      running_stats: dict[frameid] -> {"team0":count, "team1":count, "team0pct":..., "team1pct":...}
    """

    # Group by frame
    frames = defaultdict(list)
    for r in records:
        frames[int(r["frameid"])].append(r)

    frame_possession: Dict[int, Optional[int]] = {}
    running_counts = {"team0": 0, "team1": 0}
    running_stats: Dict[int, Dict[str, float]] = {}

    sorted_frame_ids = sorted(frames.keys())

    for fid in sorted_frame_ids:
        recs = frames[fid]
        # find ball(s) and players in this frame
        balls = [r for r in recs if r.get("classid") == BALL_CLASS_ID or r.get("classname") == "ball"]
        players = [r for r in recs if r.get("classname") in ("player", "goalkeeper")]
        # filter out referees if classid flagged
        players = [p for p in players if p.get("classid") != REFEREE_CLASS_ID]

        chosen_team = None

        if balls and players:
            # take first ball (common case)
            ball_c = bbox_center(balls[0]["bbox"])
            # find nearest player and its team
            best_d = None
            best_track = None
            for p in players:
                # skip invalid bbox
                bbox = p.get("bbox")
                if not bbox or len(bbox) < 4:
                    continue
                pcenter = bbox_center(bbox)
                d = euclidean(pcenter, ball_c)
                if best_d is None or d < best_d:
                    best_d = d
                    best_track = p.get("trackid")

            if best_track is not None and best_d is not None:
                # determine team for best_track using team_ids mapping
                team = team_ids.get(int(best_track), None)
                # dynamic threshold: use global POSSESSION_THRESHOLD but scale by player bbox size
                # compute player bbox size if available
                player_bbox = next((p.get("bbox") for p in players if int(p.get("trackid")) == int(best_track)), None)
                if player_bbox:
                    p_w = abs(player_bbox[2] - player_bbox[0])
                    p_h = abs(player_bbox[3] - player_bbox[1])
                    adaptive_thresh = max(POSSESSION_THRESHOLD, 0.6 * max(p_w, p_h))
                else:
                    adaptive_thresh = POSSESSION_THRESHOLD

                if team is not None and best_d <= adaptive_thresh:
                    chosen_team = int(team)

        # Update counts
        if chosen_team is None:
            # no possession assigned this frame
            pass
        elif chosen_team == 0:
            running_counts["team0"] += 1
        elif chosen_team == 1:
            running_counts["team1"] += 1

        # store per-frame possession
        frame_possession[fid] = chosen_team

        # compute running percentages (based on frames considered so far)
        total = running_counts["team0"] + running_counts["team1"]
        if total > 0:
            team0pct = round(100.0 * running_counts["team0"] / total, 1)
            team1pct = round(100.0 * running_counts["team1"] / total, 1)
        else:
            team0pct = 0.0
            team1pct = 0.0

        running_stats[fid] = {
            "team0": running_counts["team0"],
            "team1": running_counts["team1"],
            "team0pct": team0pct,
            "team1pct": team1pct,
        }

    return frame_possession, running_stats