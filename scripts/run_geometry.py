# scripts/run_geometry.py
import json
from src.geometry import run_pipeline, compute_homography

VIDEO = "input_videos/08fd33_4.mp4"
TRACKS = "outputs/tracks.json"         # ask Person 1 to produce this
OUT_JSON = "outputs/tracks_geo.json"
OUT_CSV  = "outputs/trajectories.csv"
DEBUGVID = "outputs/debug_stabilized.mp4"
CALIB = "config/calib.json"

def load_calib(path):
    try:
        with open(path,'r') as f:
            c = json.load(f)
        if 'src_pts' in c and 'dst_pts' in c:
            return compute_homography(c['src_pts'], c['dst_pts'])
    except Exception:
        pass
    return None

if __name__ == "__main__":
    H = load_calib(CALIB)
    run_pipeline(VIDEO, TRACKS, OUT_JSON, OUT_CSV, debug_video_path=DEBUGVID, homography=H)