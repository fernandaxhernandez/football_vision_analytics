# match_analysis/jersey_clustering.py

from collections import defaultdict
from typing import Dict, List, Tuple, Any

import cv2
import numpy as np
from sklearn.cluster import KMeans

from .config import BALL_CLASS_ID, REFEREE_CLASS_ID, KMEANS_RUNS  # [file:46]


def extract_jersey_pixels(img: np.ndarray, bbox: List[float]) -> np.ndarray:
    """
    Crop a mid-jersey strip from the player bbox and return RGB pixels. [file:46]
    """
    x1, y1, x2, y2 = bbox
    crop = img[int(y1):int(y2), int(x1):int(x2)]
    if crop.size == 0:
        return np.empty((0, 3), dtype=np.uint8)

    h, w = crop.shape[:2]
    top = int(h * 0.15)
    bottom = int(h * 0.55)
    mid = crop[top:bottom, :]
    return mid.reshape(-1, 3)


def collect_jersey_samples(
    records: List[Dict[str, Any]],
) -> Dict[int, np.ndarray]:
    """
    Optimised: group by image so each file is read once, skip ball/referee,
    sample up to 10 crops per track. [file:46]
    """
    by_image: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        cls = rec.get("classid")
        if cls in (BALL_CLASS_ID, REFEREE_CLASS_ID):
            continue
        tid = rec.get("trackid", 0)
        if tid <= 0:
            continue
        by_image[rec["imagepath"]].append(rec)

    raw_pixels: Dict[int, List[np.ndarray]] = defaultdict(list)
    for img_path, recs in by_image.items():
        img = cv2.imread(img_path)
        if img is None:
            continue
        for rec in recs:
            pix = extract_jersey_pixels(img, rec["bbox"])
            if pix.size == 0:
                continue
            raw_pixels[rec["trackid"]].append(pix)

    track_pixels: Dict[int, np.ndarray] = {}
    for tid, pix_list in raw_pixels.items():
        step = max(1, len(pix_list) // 10)
        sampled = pix_list[::step][:10]
        track_pixels[tid] = np.vstack(sampled)
    return track_pixels


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """
    Convert a single RGB colour (shape (3,)) to LAB. [file:46]
    """
    rgb_img = rgb.reshape(1, 1, 3).astype(np.uint8)
    lab_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2LAB)
    return lab_img.reshape(3,).astype(np.float32)


def assign_teams_track_pixels(
    track_pixels: Dict[int, np.ndarray],
) -> Tuple[Dict[int, int], Dict[int, Tuple[int, int, int]]]:
    """
    KMeans(k=2) on per-track mean LAB colours. [file:46]

    Returns:
      team_ids: trackid -> team (0 or 1)
      team_colors: trackid -> representative RGB. [file:46]
    """
    if not track_pixels:
        return {}, {}

    track_ids = list(track_pixels.keys())
    mean_rgbs = {
        tid: track_pixels[tid].mean(axis=0).astype(np.float32)
        for tid in track_ids
    }
    X = np.array(
        [rgb_to_lab(mean_rgbs[tid]) for tid in track_ids],
        dtype=np.float32,
    )

    km = KMeans(n_clusters=2, n_init=KMEANS_RUNS, random_state=0)
    labels = km.fit_predict(X)
    print(f"KMeans inertia (lower better separation): {km.inertia_:.2f}")

    team_ids = {tid: int(labels[i]) for i, tid in enumerate(track_ids)}
    team_colors = {
        tid: tuple(int(c) for c in mean_rgbs[tid])
        for tid in track_ids
    }
    return team_ids, team_colors

