#!/usr/bin/env python
"""
AprilTag (tag36h11) pose bench test: webcam -> detect -> estimate_tag_pose
-> human-readable movement instructions. Standalone validation of pose math
and camera calibration, separate from the eventual drone-follow/MAVLind code.

Uses pupil-apriltags, a Python wrapper around the same AprilRobotics C
apriltag library the original C plan targeted (same estimate_tag_pose math,
same camera-frame convention: origin at the camera, Z out of the lens
(forward), X right, Y down).

Run calibrate.py first; this script loads its output.
"""

import math
import sys

import cv2
import numpy as np
from pupil_apriltags import Detector

CAMERA_INDEX = 0
TAG_FAMILY = "tag36h11"

# Measured from where the tag's black and white borders meet, in meters.
# MUST be set before results mean anything.
TAG_SIZE_M = 0.13

CALIBRATION_FILE = "camera_calibration.npz"
DEADZONE_M = 0.05  # ignore movement/reprints smaller than this
SIGNIFICANT_M = 0.05  # below this on an axis, that axis isn't worth mentioning


def load_calibration(path: str) -> tuple[np.ndarray, np.ndarray]:
    try:
        data = np.load(path)
    except FileNotFoundError:
        print(f"{path} not found. Run calibrate.py first.")
        sys.exit(1)
    return data["camera_matrix"], data["dist_coeffs"]


def build_instruction(x: float, z: float) -> str:
    forward_significant = z > SIGNIFICANT_M
    lateral_significant = abs(x) > SIGNIFICANT_M
    direction = "right" if x > 0 else "left"

    if forward_significant and lateral_significant:
        straight_line = math.hypot(x, z)
        return (f"Move forward {z:.2f}m and {direction} {abs(x):.2f}m "
                f"(straight-line distance: {straight_line:.2f}m)")
    if forward_significant:
        return f"Move {z:.2f} meters forward"
    if lateral_significant:
        return f"Move {abs(x):.2f} meters {direction}"
    return "Tag is centered and close - no significant movement needed"


def main() -> int:
    if TAG_SIZE_M <= 0.0:
        print("Set TAG_SIZE_M at the top of this file (measured tag size in meters) before running.")
        return 1

    camera_matrix, dist_coeffs = load_calibration(CALIBRATION_FILE)
    fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
    cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Could not open camera index {CAMERA_INDEX}.")
        return 1

    detector = Detector(families=TAG_FAMILY)

    last_x: float | None = None
    last_z: float | None = None
    tag_visible = False
    current_instruction = ""

    print("Press q/ESC to quit.")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera read failed.")
            break

        # estimate_tag_pose assumes an ideal pinhole model and ignores lens
        # distortion, so undistorting first is what makes the calibration
        # step actually matter for accuracy.
        undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
        gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

        detections = detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=(fx, fy, cx, cy),
            tag_size=TAG_SIZE_M,
        )

        display = undistorted
        if detections:
            detection = detections[0]
            x, y, z = detection.pose_t.flatten()

            if not tag_visible or last_x is None or last_z is None or \
                    math.hypot(x - last_x, z - last_z) > DEADZONE_M:
                current_instruction = build_instruction(x, z)
                print(current_instruction)
                last_x, last_z = x, z
            tag_visible = True

            corners = detection.corners.astype(int)
            cv2.polylines(display, [corners], True, (0, 200, 0), 2)
            center = tuple(detection.center.astype(int))
            cv2.circle(display, center, 4, (0, 0, 255), -1)
            cv2.putText(display, f"X={x:.2f} Y={y:.2f} Z={z:.2f}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display, current_instruction,
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            if tag_visible:
                print("Tag lost")
            tag_visible = False
            last_x, last_z = None, None
            current_instruction = ""

        cv2.imshow("AprilTag Pose Test", display)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
