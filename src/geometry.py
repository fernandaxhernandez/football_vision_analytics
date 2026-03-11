# src/geometry.py
import json
import cv2
import numpy as np
from tqdm import tqdm
from collections import defaultdict
import math
import os

def load_tracks(path):
    with open(path, 'r') as f:
        return json.load(f)

def bbox_center(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)

def write_json(path, data):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path,'w') as f:
        json.dump(data, f, indent=2)

def write_csv(path, rows, header):
    import csv
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path,'w',newline='') as f:
        w=csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

# -------------------------
# Camera motion (stabilization)
# -------------------------
def estimate_frame_transforms(video_path, max_corners=200, lk_params=None):
    """
    Returns list of 2x3 affine transforms mapping points in frame t -> frame t+1
    (i.e. T_t such that p_{t+1} ≈ T_t @ [p_t,1])
    """
    if lk_params is None:
        lk_params = dict(winSize=(21,21), maxLevel=3,
                         criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    cap = cv2.VideoCapture(video_path)
    ok, prev = cap.read()
    if not ok:
        raise RuntimeError("cannot open video")
    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    transforms = []
    frame_idx = 0
    p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, maxCorners=max_corners, qualityLevel=0.01, minDistance=8)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if p0 is None or len(p0) < 10:
            # re-detect
            p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, maxCorners=max_corners, qualityLevel=0.01, minDistance=8)
        p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, p0, None, **lk_params)
        if p1 is None or st is None:
            # fallback to identity
            transforms.append(np.array([[1,0,0],[0,1,0]], dtype=np.float32))
        else:
            good0 = p0[st.flatten()==1]
            good1 = p1[st.flatten()==1]
            if len(good0) >= 3:
                # estimate robust affine
                M, inliers = cv2.estimateAffinePartial2D(good0, good1, method=cv2.RANSAC, ransacReprojThreshold=3.0)
                if M is None:
                    M = np.array([[1,0,0],[0,1,0]], dtype=np.float32)
                transforms.append(M)
            else:
                transforms.append(np.array([[1,0,0],[0,1,0]], dtype=np.float32))
        prev_gray = frame_gray.copy()
        p0 = good1.reshape(-1,1,2) if (p1 is not None and st is not None) else None
        frame_idx += 1
    cap.release()
    return transforms

def accumulate_transforms(transforms):
    """Given list of 2x3 transforms T_t (t->t+1), return cumulative transforms from frame 0 -> frame t"""
    cum = [np.eye(3)]
    cur = np.eye(3)
    for M in transforms:
        M3 = np.vstack([M, [0,0,1]])
        cur = M3 @ cur
        cum.append(cur.copy())
    return cum  # len = n_frames

# -------------------------
# Perspective / world mapping
# -------------------------
def compute_homography(src_pts, dst_pts):
    """
    src_pts: list of 4 (x,y) in image (pixel) coordinates (e.g. pitch corners)
    dst_pts: corresponding 4 (X,Y) in world plan coordinates (meters)
    returns 3x3 homography H mapping image -> world plane
    """
    src = np.array(src_pts, dtype=np.float32)
    dst = np.array(dst_pts, dtype=np.float32)
    H, status = cv2.findHomography(src, dst, method=0)
    return H

def apply_homography_to_point(H, pt):
    x,y = pt
    v = np.array([x,y,1.0])
    w = H @ v
    return (w[0]/w[2], w[1]/w[2])

# -------------------------
# Main pipeline
# -------------------------
def run_pipeline(video_path, tracks_json_path, out_json_path, out_csv_path,
                 debug_video_path=None, fps_override=None,
                 homography=None, transforms=None):
    """
    homography: 3x3 numpy (image->world meters). If None, pipeline will skip world conversion.
    transforms: precomputed per-frame transforms (2x3 list). If None, estimate from video.
    """
    tracks = load_tracks(tracks_json_path)
    # Group tracks per frame
    frames = defaultdict(list)
    for obj in tracks:
        frames[int(obj['frame'])].append(obj)
    # prepare transforms
    cap = cv2.VideoCapture(video_path)
    fps = fps_override if fps_override is not None else (cap.get(cv2.CAP_PROP_FPS) or 25.0)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if transforms is None:
        transforms = estimate_frame_transforms(video_path)
    cum = accumulate_transforms(transforms)  # cum[t] maps points in frame 0 -> frame t
    # We'll use inverse cumulative to map p_t -> stabilized coordinates (compensate camera)
    inv_cum = [np.linalg.inv(M) for M in cum]  # map frame t -> frame 0
    # build track dictionary
    per_track = defaultdict(list)  # track_id -> list of (frame, pos_pixel, pos_corr, pos_world)
    augmented = []
    # iterate frames and objects
    for frame_idx in range(n_frames):
        objs = frames.get(frame_idx, [])
        for o in objs:
            bbox = o.get('bbox')
            if bbox is None and 'center' in o:
                cx,cy = o['center']
            elif bbox is not None:
                cx,cy = bbox_center(bbox)
            else:
                continue
            pos_pixel = (float(cx), float(cy))
            # correct for camera motion: map pixel -> stabilized reference by applying inv_cum[frame]
            M = inv_cum[min(frame_idx, len(inv_cum)-1)]
            px = np.array([pos_pixel[0], pos_pixel[1], 1.0])
            p_corr = M @ px
            position_corrected = (float(p_corr[0]/p_corr[2]), float(p_corr[1]/p_corr[2]))
            # map to world coordinates (meters) if homography provided
            if homography is not None:
                pos_world = apply_homography_to_point(homography, position_corrected)
            else:
                pos_world = None
            track_id = int(o['track_id'])
            per_track[track_id].append((frame_idx, position_corrected, pos_world))
            # copy and attach fields
            new_o = dict(o)
            new_o['position_pixel'] = [pos_pixel[0], pos_pixel[1]]
            new_o['position_corrected'] = [position_corrected[0], position_corrected[1]]
            new_o['position_world'] = list(pos_world) if pos_world is not None else None
            augmented.append(new_o)
    # compute speeds and cumulative distances per track
    results_by_track = {}
    for tid, seq in per_track.items():
        seq_sorted = sorted(seq, key=lambda x: x[0])
        speeds = []
        total_m = 0.0
        prev_world = None
        prev_frame = None
        for frame_idx, pos_corr, pos_world in seq_sorted:
            speed_kmh = None
            if prev_world is not None and pos_world is not None:
                dx = pos_world[0] - prev_world[0]
                dy = pos_world[1] - prev_world[1]
                dist_m = math.hypot(dx, dy)
                dt = (frame_idx - prev_frame) / fps
                if dt > 0:
                    speed_ms = dist_m / dt
                    speed_kmh = speed_ms * 3.6
                    total_m += dist_m
            speeds.append((frame_idx, pos_world, speed_kmh, total_m))
            prev_world = pos_world
            prev_frame = frame_idx
        results_by_track[tid] = speeds
    # attach speeds back to augmented objects
    # build map for quick lookup
    speed_map = {}
    for tid, seq in results_by_track.items():
        for frame_idx, pos_world, speed_kmh, total_m in seq:
            speed_map[(tid, frame_idx)] = (speed_kmh, total_m)
    final_aug = []
    for o in augmented:
        tid = int(o['track_id'])
        f = int(o['frame'])
        s = speed_map.get((tid, f), (None, None))
        o['speed_kmh'] = s[0]
        o['total_distance_m'] = s[1]
        final_aug.append(o)
    # write outputs
    write_json(out_json_path, final_aug)
    # CSV with per-track time series
    rows = []
    header = ['track_id','frame','x_px','y_px','x_corr','y_corr','x_m','y_m','speed_kmh','total_distance_m']
    for o in final_aug:
        xpx,ypx = o.get('position_pixel') or (None,None)
        xc,yc = o.get('position_corrected') or (None,None)
        world = o.get('position_world') or (None,None)
        rows.append([o['track_id'], o['frame'], xpx, ypx, xc, yc, world[0] if world else None, world[1] if world else None, o.get('speed_kmh'), o.get('total_distance_m')])
    write_csv(out_csv_path, rows, header)
    print(f"Wrote {out_json_path} and {out_csv_path}")
    # (Optional) create debug video overlaying corrected positions
    if debug_video_path:
        cap = cv2.VideoCapture(video_path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fpsv = cap.get(cv2.CAP_PROP_FPS) or fps
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(debug_video_path, fourcc, fpsv, (w,h))
        frame_idx = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # draw all objects at this frame
            for o in final_aug:
                if int(o['frame']) == frame_idx:
                    x,y = o['position_corrected'][:2]
                    cv2.circle(frame, (int(round(x)), int(round(y))), 4, (0,255,0), -1)
                    tid = o['track_id']
                    if o.get('speed_kmh') is not None:
                        txt = f"{tid}:{0 if o.get('speed_kmh') is None else round(o.get('speed_kmh'),1)}km/h"
                    else:
                        txt = f"{tid}"
                    cv2.putText(frame, txt, (int(round(x))+5, int(round(y))-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255),1,cv2.LINE_AA)
            out.write(frame)
            frame_idx += 1
        cap.release()
        out.release()
        print("Wrote debug video", debug_video_path)