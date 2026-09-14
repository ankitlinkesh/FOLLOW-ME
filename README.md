# AprilTag Pose Test

##setup
cd into your project folder and run:
python -m venv venv
venv\Scripts\pip install -r requirements.txt

## 1. Print a chessboard and a tag
*Chessboard** (for calibration): any standard chessboard with 9x6
  internal corners works with the defaults below,use the given pattern.png from 
  (https://github.com/opencv/opencv/blob/4.x/doc/pattern.png).
  Print it flat, no scaling ("fit to page" is fine as long as you measure
  the actual printed square size afterward).
**AprilTag**: print the given tag_1 from the
  [AprilRobotics tag image repo](https://github.com/AprilRobotics/apriltag-imgs).

## 2. Measure and configure

- Measure one **chessboard square's side length** in meters with calipers or
  a ruler, and set `SQUARE_SIZE_M` in `calibrate.py` to match.
- Measure your printed **tag's black/white border-to-border size** (not the
  outer white margin) in meters, and set `TAG_SIZE_M` in `pose_test.py`.
  `pose_test.py` refuses to run until this is set.
- If `BOARD_COLS`/`BOARD_ROWS` in `calibrate.py` don't match your printed
  chessboard's internal corner count, update them too.

  ## 3. Calibrate

run "venv\Scripts\python calibrate.py" inside your project folder
Move the chessboard around (different distances, angles, tilts, corners of
the frame) and press SPACE each time it's detected (shown in green).
Capture 15-20+ views, then press ESC/q. Check the printed RMS reprojection
error — under ~0.5px is good, over ~1.0px means recapture with more/better
 varied views before trusting any pose numbers. This writes
`camera_calibration.npz`.

  ## 4. Run the pose test

venv\Scripts\python pose_test.py

Hold the tag in view. The console prints movement instructions whenever the
tag moves more than the 5cm deadzone (`DEADZONE_M` in `pose_test.py`) since
the last printed instruction, so jitter doesn't spam the console. The video
window overlays the detected tag outline, raw X/Y/Z, and the current
instruction. Quit with `q` or ESC.
  
