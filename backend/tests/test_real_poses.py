"""Regression fixtures: ONE person's measurements of six poses.

Values were read from the live readout (rounded to 2 decimals / whole degrees),
on one MacBook Air webcam, one hand, one room. They are NOT a general dataset.
They prove that today's thresholds agree with this person's hand, nothing more.
"""
import pytest

from backend.app.vision.feature_extractor import HandFeatures
from backend.app.vision.gesture_classifier import Gesture, classify

# name: (reach idx/mid/ring/pinky, thumb_reach, pip angles idx/mid/ring/pinky,
#        pinch_ratio, pinch_active, expected)
POSES = {
    "open_palm": ((1.88, 1.95, 1.81, 1.55), 1.40, (176, 180, 176, 175), 1.30, False, Gesture.OPEN_PALM),
    "fist":      ((0.81, 0.62, 0.49, 0.55), 1.00, (3, 10, 16, 36),      0.45, False, Gesture.FIST),
    "point":     ((2.25, 0.58, 0.45, 0.46), 0.83, (180, 25, 38, 61),    1.15, False, Gesture.POINT),
    "pinch":     ((1.40, 0.56, 0.43, 0.40), 1.23, (165, 89, 89, 97),    0.12, True,  Gesture.PINCH),
    "shaka":     ((0.69, 0.58, 0.56, 1.78), 1.64, (18, 4, 3, 176),      1.00, False, Gesture.SHAKA),
    "relaxed":   ((1.62, 1.70, 1.56, 1.30), 0.97, (156, 161, 149, 140), 0.40, False, Gesture.NONE),
}


def features_from(reach, thumb, angles, ratio):
    names = ("index", "middle", "ring", "pinky")
    return HandFeatures(
        hand_scale_px=100.0,
        pinch_ratio=ratio,
        reach=dict(zip(names, reach)),
        thumb_reach=thumb,
        pip_angle_deg=dict(zip(names, map(float, angles))),
        orientation_deg=0.0,
        index_tip_rel=(0.0, -1.0),
    )


@pytest.mark.parametrize("name", POSES)
def test_measured_pose_is_classified_as_expected(name):
    reach, thumb, angles, ratio, pinch_active, expected = POSES[name]
    f = features_from(reach, thumb, angles, ratio)
    assert classify(f, pinch_active) == expected


def test_relaxed_hand_is_never_open_palm():
    """A relaxed hand must not trigger Pause by accident."""
    reach, thumb, angles, ratio, _, _ = POSES["relaxed"]
    assert classify(features_from(reach, thumb, angles, ratio), False) != Gesture.OPEN_PALM
