# match_analysis/annotate.py

from typing import Dict, List, Any, Tuple

from .config import REFEREE_CLASS_ID, BALL_CLASS_ID  # [file:46]


def annotate_records(
    records: List[Dict[str, Any]],
    team_ids: Dict[int, int],
    team_colors: Dict[int, Tuple[int, int, int]],
    frame_possession: Dict[int, int | None],
    running_stats: Dict[int, Dict[str, float | int]],
) -> List[Dict[str, Any]]:
    """
    Add teamid, teamcolor, hasball, possessionstats to each record. [file:46]
    """
    annotated: List[Dict[str, Any]] = []

    for rec in records:
        r = dict(rec)
        fid = r["frameid"]
        tid = r["trackid"]

        if tid == BALL_CLASS_ID or r.get("classid") == REFEREE_CLASS_ID:
            r["teamid"] = None
            r["teamcolor"] = None
            r["hasball"] = False
        else:
            r["teamid"] = team_ids.get(tid)
            r["teamcolor"] = team_colors.get(tid)
            r["hasball"] = (frame_possession.get(fid) == tid)

        r["possessionstats"] = running_stats.get(fid)
        annotated.append(r)

    return annotated

