# football_vision_analytics

football-vision-analytics/
│
├── app/
│   ├── landing.py
│   ├── main_app.py
│
├── src/
│   ├── detection.py
│   ├── tracking.py
│   ├── team_assignment.py
│   ├── motion.py
│   ├── metrics.py
│   ├── agent.py
│
├── scripts/
│   ├── train_yolo.py
│   ├── run_inference.py
│
├── configs/
│   ├── yolo_config.yaml
│
├── data/
│
├── models/
│
├── requirements.txt
├── README.md


# Geometry & Speed Analytics (Hildana)
## Objective

### My responsibility in this project was to transform tracked player detections into real-world football analytics by:
- Compensating for camera movement
- converting pixel coordinates into real-world pitch coordinates (meters)
- Computing player speed (km/h)
- Computing total distance covered (meters)
- This layer converts raw tracking output into measurable performance metrics.


### This module consumes:

- outputs/tracks.json
Produced by the detection & tracking layer.

- Each entry contains:

{
  "frame": 10,
  "track_id": 4,
  "bbox": [x1, y1, x2, y2],
  "object_type": "player"
}

## Processing Pipeline

### The geometry pipeline performs the following steps:

- Camera Motion Estimation

Because broadcast football footage includes camera panning and zooming, raw pixel movement does not represent true player movement.
- To correct this:
- Optical flow (Lucas-Kanade) is applied between frames
- A robust affine transformation (RANSAC) is estimated

- Object positions are stabilized relative to a reference frame

- This produces:

"position_corrected": [x, y]

Which removes camera-induced motion.

## Ground-Plane Projection (Homography)

Pixel coordinates are converted into real-world pitch coordinates using a homography transformation.
Calibration is stored in:
- config/calib.json

Example:

{
  "src_pts": [[453,269],[1754,229],[1911,897],[551,986]],
  "dst_pts": [[52.5,0],[105,0],[105,68],[52.5,68]]
}

This maps selected pitch line intersections in the image to real pitch dimensions (meters).

- After transformation, each player has:

"position_world": [x_meters, y_meters]

## Foot-Point Projection

Instead of using the bounding box center, the bottom-center of the bounding box is used:

((x1 + x2) / 2, y2)

This approximates the player’s foot position on the pitch, improving geometric accuracy.

## Speed Calculation

Speed is computed using:

- distance / time

- Where:

- Distance is computed between world coordinates (meters)

- Time is derived from video FPS

- Converted to km/h

Output:

"speed_kmh": 18.7

## Distance Covered

Cumulative distance per player is tracked over time:

"total_distance_m": 124.3

## Output of This Module

Running:

python -m scripts.run_geometry

Produces:

outputs/tracks_geo.json

Enhanced tracking data containing:

position_pixel

position_corrected

position_world

speed_kmh

total_distance_m

outputs/trajectories.csv

Structured analytics table for further analysis or visualization.

outputs/debug_stabilized.mp4

Debug video showing stabilized tracking overlays.

## What This Enables

This module enables:

Real-world player movement tracking

Speed profiling (km/h)

Distance covered metrics

Accurate analytics independent of camera motion

Without this step, tracking would only provide pixel movement, which is not physically meaningful.

## Key Techniques Used

Optical Flow (Lucas-Kanade)

Affine Transformation with RANSAC

Homography & Perspective Transformation

Ground-plane projection

Kinematic speed computation

## Summary

This component transforms raw object tracking into structured football performance data.

It bridges computer vision outputs and sports analytics metrics.

## What I added to the original folder structure( Hildana )

FOOTBALL_VISION_ANALYTICS/
│
├── config/
│   └── calib.json                # Homography calibration (pixel → meters)
│
├── input_videos/
│   └── 08fd33_4.mp4              # Match footage input
│
├── outputs/
│   ├── tracks.json               # Raw tracking results (input to my module)
│   ├── tracks_geo.json           # Augmented analytics output
│   ├── trajectories.csv          # Structured speed & distance data
│   └── debug_stabilized.mp4      # Visualization for validation
│
├── scripts/
│   ├── run_geometry.py           # Entry point for geometry pipeline
│   └── calibrate.py              # Calibration tool (homography setup)
│
├── src/
│   └── geometry.py               # Core geometry + speed logic (main file)
│
└── README.md