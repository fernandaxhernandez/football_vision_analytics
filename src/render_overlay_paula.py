# src/render_overlay_paula.py
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict
import cv2


def load_by_frame(annotated_json: Path):
    data = json.loads(annotated_json.read_text(encoding="utf-8"))
    by_frame = defaultdict(list)
    for r in data:
        by_frame[int(r["frameid"])].append(r)
    return by_frame


def draw_overlay(
    video_path: Path,
    annotated_json: Path,
    out_path: Path,
    show_possession_text: bool = True,
):
    if not video_path.exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")
    if not annotated_json.exists():
        raise FileNotFoundError(f"JSON no encontrado: {annotated_json}")

    by_frame = load_by_frame(annotated_json)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"No pude abrir video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

    last_stats = None

    frame_id = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        recs = by_frame.get(frame_id, [])

        # Draw bboxes
        for r in recs:
            cls = r.get("classname")
            bbox = r.get("bbox")
            if not bbox:
                continue
            x1, y1, x2, y2 = map(int, bbox)

            if cls in ("player", "goalkeeper"):
                teamcolor = r.get("teamcolor", [0, 255, 0])  # [R,G,B]
                # OpenCV usa BGR
                bgr = (int(teamcolor[2]), int(teamcolor[1]), int(teamcolor[0]))
                teamid = r.get("teamid", -1)

                cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                label = f"T{teamid}#{r.get('trackid', -1)}"
                cv2.putText(frame, label, (x1, max(20, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgr, 2, cv2.LINE_AA)

                # marca si tiene balón
                if r.get("hasball", False):
                    cv2.circle(frame, (x1 + 8, y1 + 8), 8, bgr, -1)

            elif cls == "ball":
                # bola: círculo amarillo
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                cv2.circle(frame, (cx, cy), 6, (0, 255, 255), -1)
                cv2.circle(frame, (cx, cy), 12, (0, 255, 255), 2)

            # stats (vienen repetidos en records; usamos el último)
            if "possessionstats" in r:
                last_stats = r["possessionstats"]

        # Draw possession text top bar
        if show_possession_text and last_stats is not None:
            t0 = float(last_stats.get("team0pct", 0.0))
            t1 = float(last_stats.get("team1pct", 0.0))

            # barra simple
            bar_w = int(w * 0.35)
            bar_h = 18
            x0, y0 = 12, 12
            cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h), (30, 30, 30), -1)

            # Team0 (verde)
            t0w = int(bar_w * (t0 / 100.0))
            cv2.rectangle(frame, (x0, y0), (x0 + t0w, y0 + bar_h), (80, 200, 120), -1)
            # Team1 (gris claro)
            cv2.rectangle(frame, (x0 + t0w, y0), (x0 + bar_w, y0 + bar_h), (170, 170, 170), -1)

            text = f"Possession  T0 {t0:.1f}% | T1 {t1:.1f}%"
            cv2.putText(frame, text, (x0, y0 + bar_h + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        writer.write(frame)
        frame_id += 1

        # mini progreso cada 100 frames
        if frame_id % 100 == 0:
            print(f"[overlay] frame {frame_id}/{total}")

    cap.release()
    writer.release()
    print(f"✅ Overlay video guardado en: {out_path}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--video", default="input_videos/08fd33_4.mp4")
    p.add_argument("--json", default="outputs/tracks_annotated_paula.json")
    p.add_argument("--out", default="outputs/08fd33_4_overlay.mp4")
    args = p.parse_args()

    draw_overlay(Path(args.video), Path(args.json), Path(args.out))