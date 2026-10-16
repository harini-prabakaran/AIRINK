"""Hand tracking. Wraps MediaPipe HandLandmarker.

This module knows nothing about web servers or browsers. It takes an RGB image
and returns a TrackingResult. Coordinates are normalised (0-1) and UNMIRRORED,
exactly as MediaPipe reports them.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

logger = logging.getLogger("airink.tracker")

NUM_LANDMARKS = 21


@dataclass(frozen=True)
class TrackingResult:
    hand_detected: bool
    # 21 (x, y, z) tuples when a hand is detected, otherwise an empty list.
    landmarks: list[tuple[float, float, float]]
    # MediaPipe's Left/Right classification score. NOT a gesture confidence.
    handedness_score: float | None
    timestamp_ms: int


class HandTracker:
    def __init__(
        self,
        model_path: Path,
        num_hands: int = 1,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"MediaPipe model not found at {model_path}")

        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        # Created ONCE here, reused for every frame.
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1
        logger.info("HandTracker initialised")

    def process(self, frame_rgb: np.ndarray, timestamp_ms: int) -> TrackingResult:
        """Run hand tracking on one RGB frame (H x W x 3, uint8)."""
        if frame_rgb is None or frame_rgb.ndim != 3 or frame_rgb.shape[2] != 3:
            raise ValueError("frame_rgb must be an H x W x 3 array")

        # VIDEO mode requires strictly increasing timestamps.
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(frame_rgb),
        )
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return TrackingResult(False, [], None, timestamp_ms)

        hand = result.hand_landmarks[0]
        if len(hand) != NUM_LANDMARKS:
            logger.warning("Expected %d landmarks, got %d", NUM_LANDMARKS, len(hand))
            return TrackingResult(False, [], None, timestamp_ms)

        landmarks = [(lm.x, lm.y, lm.z) for lm in hand]
        score = result.handedness[0][0].score if result.handedness else None
        return TrackingResult(True, landmarks, score, timestamp_ms)

    def close(self) -> None:
        self._landmarker.close()
        logger.info("HandTracker closed")
