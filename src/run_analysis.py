# src/run_analysis.py
from __future__ import annotations

from pathlib import Path
import uuid

from src.render_overlay_paula import draw_overlay


def run_analysis(video_path: Path, annotated_json: Path) -> Path:
    """
    Produce overlay mp4 from a given video and Paula annotated json.
    Returns output video path.
    """
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)

    out_path = out_dir / f"{video_path.stem}_overlay_{uuid.uuid4().hex[:8]}.mp4"
    draw_overlay(video_path, annotated_json, out_path, show_possession_text=True)
    return out_path