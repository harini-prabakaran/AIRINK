"""Day 1: run MediaPipe Hand Landmarker on one image and print the landmarks."""
import sys
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL = REPO_ROOT / "models" / "hand_landmarker.task"

LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
]


def main(image_path: str) -> None:
    if not MODEL.exists():
        sys.exit(f"Model not found at {MODEL}. Download it first.")
    if not Path(image_path).exists():
        sys.exit(f"Image not found: {image_path}")

    options = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL)),
        num_hands=1,
        running_mode=vision.RunningMode.IMAGE,
    )
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        image = mp.Image.create_from_file(image_path)
        result = landmarker.detect(image)

    if not result.hand_landmarks:
        sys.exit("No hand detected. Try better light or a clearer palm-facing photo.")

    hand = result.hand_landmarks[0]
    handedness = result.handedness[0][0]
    print(f"Detected: {handedness.category_name} (score {handedness.score:.2f})")
    print(f"Landmarks: {len(hand)}\n")
    for name, lm in zip(LANDMARK_NAMES, hand):
        print(f"{name:11s} x={lm.x:.3f} y={lm.y:.3f} z={lm.z:+.3f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "experiments/data/test_hand.jpg")
