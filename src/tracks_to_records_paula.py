# src/tracks_to_records_paula.py
from __future__ import annotations

import argparse
import json
from pathlib import Path


# Debe match con tu tracking_export.py
NAME_TO_CLASSID = {
    "ball": 0,
    "goalkeeper": 1,
    "player": 2,
    "referee": 3,
}


def convert(tracks_json: Path, frames_dir: Path, out_json: Path) -> None:
    data = json.loads(tracks_json.read_text(encoding="utf-8"))
    tracks = data["tracks"]

    frames_dir = Path(frames_dir)
    out: list[dict] = []

    for fr in tracks:
        frameid = int(fr["frame_id"])
        imagepath = (frames_dir / f"frame_{frameid:06d}.jpg").as_posix()

        for obj in fr.get("objects", []):
            classname = obj["object_type"]
            classid = NAME_TO_CLASSID.get(classname, -1)

            record = {
                "frameid": frameid,
                "classid": classid,
                "classname": classname,
                "trackid": int(obj.get("track_id", -1)),
                "bbox": obj["bbox"],                 # xyxy float
                "conf": float(obj.get("confidence", 0.0)),
                "imagepath": imagepath,              # Paula usa cv2.imread(imagepath)
            }
            out.append(record)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ records_paula.json creado: {out_json}")
    print(f"   Total records: {len(out)}")
    print(f"   Example record: {out[0] if out else 'EMPTY'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--tracks", default="outputs/tracks.json")
    p.add_argument("--frames_dir", default="outputs/frames")
    p.add_argument("--out", default="outputs/records_paula.json")
    args = p.parse_args()

    convert(Path(args.tracks), Path(args.frames_dir), Path(args.out))