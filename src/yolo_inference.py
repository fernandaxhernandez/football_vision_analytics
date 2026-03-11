import os
import json
from ultralytics import YOLO

VIDEO_PATH = "input_videos/08fd33_4.mp4"
OUT_DIR = "outputs"
OUT_JSON = os.path.join(OUT_DIR, "tracks.json")

os.makedirs(OUT_DIR, exist_ok=True)

model = YOLO("yolov8x.pt")

# IMPORTANT:
# - use track(), not predict()
# - persist=True keeps IDs consistent across frames
# - save=True saves annotated video frames (optional)
results = model.track(
    source=VIDEO_PATH,
    persist=True,
    save=True,
    stream=True,   # stream=True yields results frame-by-frame (good for videos)
    verbose=False
)

tracks_output = []

for frame_idx, r in enumerate(results):
    if r.boxes is None:
        continue

    for b in r.boxes:
        # If tracker couldn't assign an ID, skip it
        if b.id is None:
            continue

        track_id = int(b.id.item())
        cls_id = int(b.cls.item()) if b.cls is not None else -1
        conf = float(b.conf.item()) if b.conf is not None else None

        x1, y1, x2, y2 = b.xyxy[0].tolist()

        # label name from model (COCO names if using yolov8x.pt)
        name = model.names.get(cls_id, str(cls_id))

        tracks_output.append({
            "frame": frame_idx,
            "track_id": track_id,
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "object_type": name,
            "confidence": conf
        })

with open(OUT_JSON, "w") as f:
    json.dump(tracks_output, f, indent=2)

print(f"Saved {OUT_JSON} with {len(tracks_output)} entries.")