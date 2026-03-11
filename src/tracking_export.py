# src/tracking_export.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import cv2
from ultralytics import YOLO

# Orden de clases según tu dataset:
# names: [ball, goalkeeper, player, referee]
CLASS_MAP = {
    0: "ball",
    1: "goalkeeper",
    2: "player",
    3: "referee",
}


@dataclass
class TrackExportConfig:
    model_path: Path = Path("models/best.pt")
    output_dir: Path = Path("outputs")
    conf: float = 0.30
    imgsz: int = 640
    tracker: str = "bytetrack.yaml"  # también puedes usar "botsort.yaml"
    save_annotated: bool = True      # guarda video anotado para validar


def export_tracks_json(video_path: str | Path, cfg: TrackExportConfig) -> Path:
    """
    Corre YOLO + tracking (ByteTrack/BOTSort) sobre un video y exporta:
      - outputs/tracks.json (estructura por frame)
      - outputs/meta.json   (fps, dims, etc.)
      - outputs/<video>_annotated.mp4 (opcional)
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")

    if not cfg.model_path.exists():
        raise FileNotFoundError(f"Modelo no encontrado: {cfg.model_path}")

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    # Leer metadata del video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"No pude abrir el video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    meta = {
        "video": str(video_path),
        "fps": fps,
        "width": width,
        "height": height,
        "total_frames": total_frames,
        "model_path": str(cfg.model_path),
        "tracker": cfg.tracker,
        "conf": cfg.conf,
        "imgsz": cfg.imgsz,
    }

    model = YOLO(str(cfg.model_path))

    # Video writer (opcional)
    out_video_path = cfg.output_dir / f"{video_path.stem}_annotated.mp4"
    writer = None

    tracks: List[Dict[str, Any]] = []

    # stream=True para procesar frame a frame
    results = model.track(
        source=str(video_path),
        conf=cfg.conf,
        imgsz=cfg.imgsz,
        tracker=cfg.tracker,
        persist=True,
        stream=True,
        verbose=False,
    )

    for frame_id, r in enumerate(results):
        frame_objects: List[Dict[str, Any]] = []

        if r.boxes is not None and len(r.boxes) > 0:
            boxes_xyxy = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            clss = r.boxes.cls.cpu().numpy().astype(int)

            ids = None
            if r.boxes.id is not None:
                ids = r.boxes.id.cpu().numpy().astype(int)

            for i in range(len(boxes_xyxy)):
                x1, y1, x2, y2 = boxes_xyxy[i].tolist()
                cls_id = int(clss[i])
                obj_type = CLASS_MAP.get(cls_id, str(cls_id))

                frame_objects.append(
                    {
                        "object_type": obj_type,
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "confidence": float(confs[i]),
                        "track_id": int(ids[i]) if ids is not None else -1,
                    }
                )

        tracks.append({"frame_id": frame_id, "objects": frame_objects})

        # Guardar video anotado (para validar)
        if cfg.save_annotated:
            frame = r.plot()  # frame con bboxes + labels
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(out_video_path), fourcc, fps, (width, height))
            writer.write(frame)

    if writer is not None:
        writer.release()

    # Guardar JSONs
    tracks_path = cfg.output_dir / "tracks.json"
    with open(tracks_path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "tracks": tracks}, f, ensure_ascii=False, indent=2)

    meta_path = cfg.output_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return tracks_path


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, help="Ruta al video de entrada (.mp4)")
    p.add_argument("--model", default="models/best.pt", help="Ruta al modelo (.pt)")
    p.add_argument("--outdir", default="outputs", help="Carpeta de salida")
    p.add_argument("--conf", type=float, default=0.30, help="Confidence threshold")
    p.add_argument("--imgsz", type=int, default=640, help="Tamaño de imagen para inferencia")
    p.add_argument("--tracker", default="bytetrack.yaml", help="bytetrack.yaml o botsort.yaml")
    p.add_argument("--no_annotated", action="store_true", help="No guardar video anotado")
    args = p.parse_args()

    cfg = TrackExportConfig(
        model_path=Path(args.model),
        output_dir=Path(args.outdir),
        conf=args.conf,
        imgsz=args.imgsz,
        tracker=args.tracker,
        save_annotated=not args.no_annotated,
    )

    out = export_tracks_json(args.video, cfg)
    print(f"✅ Export listo: {out}")