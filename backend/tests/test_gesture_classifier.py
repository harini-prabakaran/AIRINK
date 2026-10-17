import pytest

from backend.app.vision.feature_extractor import extract_features
from backend.app.vision.gesture_classifier import (
    FingerState, Gesture, classify, finger_state, finger_states, thumb_state,
)
from backend.app.vision.pinch_detector import PinchDetector

from backend.tests.hands import H, W, build_hand  # noqa: E402


def classify_hand(hand, pinch_active=None):
    f = extract_features(hand, (W, H))
    if pinch_active is None:
        pinch_active = PinchDetector().update(f.pinch_ratio) if f else False
    return classify(f, pinch_active)


# --- gestures -------------------------------------------------------------

def test_point():
    assert classify_hand(build_hand(index=True, middle=False, ring=False, pinky=False, thumb=False)) == Gesture.POINT


def test_point_with_thumb_out_is_still_point():
    assert classify_hand(build_hand(index=True, middle=False, ring=False, pinky=False, thumb=True)) == Gesture.POINT


def test_open_palm():
    assert classify_hand(build_hand()) == Gesture.OPEN_PALM


def test_fist():
    assert classify_hand(build_hand(False, False, False, False, thumb=False)) == Gesture.FIST


def test_shaka():
    assert classify_hand(build_hand(False, False, False, True, thumb=True)) == Gesture.SHAKA


def test_pinch_when_pinch_detector_is_active():
    hand = build_hand(index=True, middle=False, ring=False, pinky=False, pinch=True)
    assert classify_hand(hand) == Gesture.PINCH


def test_pinch_takes_priority_over_other_poses():
    hand = build_hand()
    f = extract_features(hand, (W, H))
    assert classify(f, pinch_active=True) == Gesture.PINCH
    assert classify(f, pinch_active=False) == Gesture.OPEN_PALM


# --- things that must NOT match -------------------------------------------

def test_open_palm_requires_thumb_not_tucked():
    assert classify_hand(build_hand(thumb=False)) != Gesture.OPEN_PALM


def test_peace_sign_is_none():
    assert classify_hand(build_hand(True, True, False, False, thumb=False)) == Gesture.NONE


def test_three_fingers_is_none():
    assert classify_hand(build_hand(True, True, True, False, thumb=False)) == Gesture.NONE


def test_shaka_needs_pinky_extended():
    assert classify_hand(build_hand(False, False, False, False, thumb=True)) != Gesture.SHAKA


def test_no_features_is_none_even_if_pinch_flag_is_set():
    assert classify(None, pinch_active=False) == Gesture.NONE
    assert classify(None, pinch_active=True) == Gesture.NONE


# --- finger / thumb state boundaries ---------------------------------------

@pytest.mark.parametrize("reach,angle,expected", [
    (1.9, 178, FingerState.EXTENDED),
    (1.45, 165, FingerState.EXTENDED),     # exactly on the extended boundary
    (1.9, 150, FingerState.UNKNOWN),       # long but bent 30 degrees: not extended
    (1.0, 40, FingerState.CURLED),
    (1.9, 100, FingerState.CURLED),        # long but sharply bent
    (1.3, 140, FingerState.UNKNOWN),       # in between: neither
])
def test_finger_state(reach, angle, expected):
    assert finger_state(reach, angle) == expected


@pytest.mark.parametrize("reach,expected", [
    (1.3, FingerState.EXTENDED), (1.10, FingerState.EXTENDED), (0.5, FingerState.CURLED), (0.9, FingerState.UNKNOWN),
])
def test_thumb_state(reach, expected):
    assert thumb_state(reach) == expected


def test_finger_states_has_all_five_digits():
    f = extract_features(build_hand(), (W, H))
    assert set(finger_states(f)) == {"index", "middle", "ring", "pinky", "thumb"}


# --- real data -------------------------------------------------------------

REAL_OPEN_HAND = [
    (0.483, 0.768, 0.000), (0.431, 0.759, -0.027), (0.381, 0.725, -0.046),
    (0.339, 0.687, -0.063), (0.302, 0.667, -0.081),
    (0.389, 0.602, -0.030), (0.351, 0.537, -0.051), (0.328, 0.495, -0.068), (0.309, 0.455, -0.081),
    (0.418, 0.572, -0.031), (0.389, 0.492, -0.049), (0.370, 0.438, -0.064), (0.352, 0.394, -0.075),
    (0.452, 0.566, -0.036), (0.430, 0.488, -0.055), (0.413, 0.435, -0.070), (0.396, 0.391, -0.080),
    (0.490, 0.576, -0.043), (0.496, 0.511, -0.059), (0.498, 0.467, -0.068), (0.497, 0.426, -0.076),
]


def test_real_open_hand_photo_is_open_palm():
    assert classify_hand(REAL_OPEN_HAND) == Gesture.OPEN_PALM
