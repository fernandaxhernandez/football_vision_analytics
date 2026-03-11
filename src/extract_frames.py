# src/extract_frames.py
from __future__ import annotations

import argparse
from pathlib import Path
import cv2


def extract_frames(video_path: Path, out_dir: Path, every_n: int = 1, max_frames: int | None = None) -> int:
    if not video_path.exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"No pude abrir el video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    saved = 0
    idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if idx % every_n == 0:
            out_path = out_dir / f"frame_{idx:06d}.jpg"
            # calidad jpeg alta para jerseys
            cv2.imwrite(str(out_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            saved += 1

            if max_frames is not None and saved >= max_frames:
                break

        idx += 1

    cap.release()
    print(f"✅ Frames guardados: {saved} / frames leídos: {idx} / total reportado: {total}")
    print(f"📁 Carpeta: {out_dir}")
    return saved


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, help="Ruta al video .mp4")
    p.add_argument("--outdir", default="outputs/frames", help="Carpeta destino de frames")
    p.add_argument("--every_n", type=int, default=1, help="Guardar 1 frame cada N")
    p.add_argument("--max_frames", type=int, default=0, help="0 = sin limite")
    args = p.parse_args()

    max_frames = None if args.max_frames == 0 else args.max_frames
    extract_frames(Path(args.video), Path(args.outdir), every_n=args.every_n, max_frames=max_frames)