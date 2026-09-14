#!/usr/bin/env python
"""
One-time camera calibration via a printed chessboard, following OpenCV's
standard findChessboardCorners -> cornerSubPix -> calibrateCamera recipe
(the same algorithm as OpenCV's own samples/python/calibrate.py, adapted
here into a live webcam capture loop instead of a folder of pre-taken
photos).

Print a chessboard pattern with BOARD_COLS x BOARD_ROWS *internal* corners
(the default 9x6 matches OpenCV's own sample pattern, e.g.
https://github.com/opencv/opencv/blob/4.x/doc/pattern.png), measure one
square's side length in meters, and set SQUARE_SIZE_M below to match.

Controls while running:
    SPACE - capture the current frame (only accepted while a board is detected)
    ESC / q - stop capturing and run calibration on what you've got

Output: camera_calibration.npz next to this script, containing
camera_matrix and dist_coeffs.
"""

import sys

import cv2
import numpy as np

CAMERA_INDEX = 0
BOARD_COLS = 9  # internal corners, i.e. squares_wide - 1
BOARD_ROWS = 6  # internal corners, i.e. squares_tall - 1
SQUARE_SIZE_M = 0.028
MIN_CAPTURES = 12
TARGET_CAPTURES = 20
OUTPUT_FILE = "camera_calibration.npz"

FIND_FLAGS = (
    cv2.CALIB_CB_ADAPTIVE_THRESH
    | cv2.CALIB_CB_FAST_CHECK
    | cv2.CALIB_CB_NORMALIZE_IMAGE
)
SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


def build_object_points() -> np.ndarray:
    objp = np.zeros((BOARD_ROWS * BOARD_COLS, 3), np.float32)
    objp[:, :2] = np.mgrid[0:BOARD_COLS, 0:BOARD_ROWS].T.reshape(-1, 2)
    objp *= SQUARE_SIZE_M
    return objp


def main() -> int:
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Could not open camera index {CAMERA_INDEX}.")
        return 1

    objp = build_object_points()
    objpoints: list[np.ndarray] = []
    imgpoints: list[np.ndarray] = []
    frame_size: tuple[int, int] | None = None

    print(f"Looking for a {BOARD_COLS}x{BOARD_ROWS}-internal-corner chessboard.")
    print("SPACE = capture (only while board is detected), ESC/q = finish and calibrate.")
    print(f"Aim for {TARGET_CAPTURES}+ captures at varied distances/angles/tilts "
          f"(minimum {MIN_CAPTURES} to calibrate at all).")

    window = "Calibration"
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera read failed.")
            break
        frame_size = (frame.shape[1], frame.shape[0])
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        found, corners = cv2.findChessboardCorners(gray, (BOARD_COLS, BOARD_ROWS), FIND_FLAGS)

        display = frame.copy()
        if found:
            cv2.drawChessboardCorners(display, (BOARD_COLS, BOARD_ROWS), corners, found)
            status_text, status_color = "Board detected - SPACE to capture", (0, 200, 0)
        else:
            status_text, status_color = "Board not detected", (0, 0, 220)

        cv2.putText(display, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(display, f"Captured: {len(objpoints)}/{TARGET_CAPTURES}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow(window, display)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break
        if key == ord(" ") and found:
            refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), SUBPIX_CRITERIA)
            objpoints.append(objp)
            imgpoints.append(refined)
            print(f"Captured {len(objpoints)}/{TARGET_CAPTURES}")

    cap.release()
    cv2.destroyAllWindows()

    if len(objpoints) < MIN_CAPTURES:
        print(f"Only {len(objpoints)} captures, need at least {MIN_CAPTURES}. "
              "Run again and capture more varied views.")
        return 1

    assert frame_size is not None
    rms_error, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(
        objpoints, imgpoints, frame_size, None, None
    )

    fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
    cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]
    print(f"\nRMS reprojection error: {rms_error:.4f} px "
          f"({'good' if rms_error < 0.5 else 'ok' if rms_error < 1.0 else 'high - recapture recommended'})")
    print(f"fx={fx:.2f}  fy={fy:.2f}  cx={cx:.2f}  cy={cy:.2f}")

    np.savez(OUTPUT_FILE, camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)
    print(f"Saved {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
