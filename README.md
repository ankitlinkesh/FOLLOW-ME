# AprilTag Pose Test

Standalone bench test: webcam + printed AprilTag (tag36h11) -> pose estimate
-> printed movement instructions ("Move 1.2 meters forward", etc). Validates
camera calibration and pose math before any drone/MAVLink code exists.

Uses [`pupil-apriltags`](https://github.com/pupil-labs/apriltags), a Python
wrapper around the same AprilRobotics `apriltag` C library and
`estimate_tag_pose()` math the eventual drone code will use in C, so the
results here (coordinate convention, pose accuracy behavior) carry over
directly.

## Setup

```powershell
cd D:\projects\AprilTag-PoseTest
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## 1. Print a chessboard and a tag

- **Chessboard** (for calibration): any standard chessboard with 9x6
  *internal* corners works with the defaults below, e.g. OpenCV's own
  [pattern.png](https://github.com/opencv/opencv/blob/4.x/doc/pattern.png).
  Print it flat, no scaling ("fit to page" is fine as long as you measure
  the actual printed square size afterward).
  or find the image attached as pattern.png
- **AprilTag**: generate/print a `tag36h11` tag, e.g. from the
  [AprilRobotics tag image repo](https://github.com/AprilRobotics/apriltag-imgs)
  (`tag36h11` folder) or any tag36h11 generator. Mount it flat (glue to
  cardboard/foam board) so it doesn't curl.
  or find the image attached as tag_1.png
## 2. Measure and configure

- Measure one **chessboard square's side length** in meters with calipers or
  a ruler, and set `SQUARE_SIZE_M` in `calibrate.py` to match.
- Measure your printed **tag's black/white border-to-border size** (not the
  outer white margin) in meters, and set `TAG_SIZE_M` in `pose_test.py`.
  `pose_test.py` refuses to run until this is set.
- If `BOARD_COLS`/`BOARD_ROWS` in `calibrate.py` don't match your printed
  chessboard's internal corner count, update them too.

## 3. Calibrate

```powershell
venv\Scripts\python calibrate.py
```

Move the chessboard around (different distances, angles, tilts, corners of
the frame) and press SPACE each time it's detected (shown in green).
Capture 15-20+ views, then press ESC/q. Check the printed RMS reprojection
error — under ~0.5px is good, over ~1.0px means recapture with more/better
varied views before trusting any pose numbers. This writes
`camera_calibration.npz`.

## 4. Run the pose test

```powershell
venv\Scripts\python pose_test.py
```

Hold the tag in view. The console prints movement instructions whenever the
tag moves more than the 5cm deadzone (`DEADZONE_M` in `pose_test.py`) since
the last printed instruction, so jitter doesn't spam the console. The video
window overlays the detected tag outline, raw X/Y/Z, and the current
instruction. Quit with `q` or ESC.

## Files

- `calibrate.py` - one-time chessboard camera calibration -> `camera_calibration.npz`
- `pose_test.py` - main bench test: detect tag, estimate pose, print instructions
- `requirements.txt` - `opencv-python`, `pupil-apriltags`, `numpy`
