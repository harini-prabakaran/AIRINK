"""Glue between landmarks and gestures: features -> pinch hysteresis -> raw gesture.

One GesturePipeline per connection, because the pinch detector is stateful.
Knows nothing about WebSockets, cameras, or MediaPipe.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .feature_extractor import HandFeatures, extract_features
from .gesture_classifier import FingerState, Gesture, classify, finger_states
from .pinch_detector import PinchDetector


@dataclass(frozen=True)
class PipelineOutput:
    features: HandFeatures | None
    finger_states: dict[str, FingerState] | None
    pinch_active: bool
    gesture: Gesture   # RAW single-frame candidate, not temporally stabilised

    def to_wire(self) -> dict:
        """JSON-safe dict for the WebSocket reply."""
        f = self.features
        features = None
        if f is not None and self.finger_states is not None:
            features = {
                "pinch_ratio": round(f.pinch_ratio, 3),
                "hand_scale_px": round(f.hand_scale_px, 1),
                "reach": {k: round(v, 3) for k, v in f.reach.items()},
                "thumb_reach": round(f.thumb_reach, 3),
                "pip_angle_deg": {k: round(v, 1) for k, v in f.pip_angle_deg.items()},
                "orientation_deg": round(f.orientation_deg, 1),
                "finger_states": {k: s.value for k, s in self.finger_states.items()},
            }
        return {
            "raw_gesture": self.gesture.value,
            "pinch_active": self.pinch_active,
            "features": features,
        }


class GesturePipeline:
    def __init__(self) -> None:
        self._pinch = PinchDetector()

    def reset(self) -> None:
        self._pinch.reset()

    def process(
        self,
        landmarks: Sequence[Sequence[float]] | None,
        frame_size: tuple[int, int],
    ) -> PipelineOutput:
        """landmarks=None means 'no hand this frame'. That RESETS the pinch state,
        so a stale pinch can never survive tracking loss."""
        features = extract_features(landmarks, frame_size) if landmarks else None
        if features is None:
            self._pinch.reset()
            return PipelineOutput(None, None, False, Gesture.NONE)
        pinch = self._pinch.update(features.pinch_ratio)
        return PipelineOutput(features, finger_states(features), pinch, classify(features, pinch))
