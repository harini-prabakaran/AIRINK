"""Day 2, Step 1: exercise HandTracker on one photo, and time it."""
import sys
import time
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import MODEL_PATH  # noqa: E402
from backend.app.vision.hand_tracker import HandTracker  # noqa: E402

image_path = sys.argv[1] if len(sys.argv) > 1 else str(REPO_ROOT / "experiments/data/test_hand.jpg")

bgr = cv2.imread(image_path)  # OpenCV loads images as BGR
if bgr is None:
    sys.exit(f"Could not read image: {image_path}")
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)  # MediaPipe expects RGB
rgb = cv2.resize(rgb, (640, 480))

t0 = time.perf_counter()
tracker = HandTracker(MODEL_PATH)
print(f"Model load time: {(time.perf_counter() - t0) * 1000:.0f} ms (paid once)")

times = []
for i in range(30):
    t = time.perf_counter()
    result = tracker.process(rgb, timestamp_ms=i * 33)
    times.append((time.perf_counter() - t) * 1000)

print(f"Hand detected: {result.hand_detected}")
if result.hand_detected:
    x, y, _ = result.landmarks[8]
    print(f"Index fingertip: x={x:.3f} y={y:.3f}")
print(f"First frame: {times[0]:.1f} ms")
print(f"Frames 2-30: mean {sum(times[1:]) / len(times[1:]):.1f} ms, max {max(times[1:]):.1f} ms")
tracker.close()
