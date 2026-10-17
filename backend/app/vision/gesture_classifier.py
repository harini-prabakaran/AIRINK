"""Single-frame, rule-based gesture candidates.

This is the RAW candidate for one frame. It is deliberately not stable:
temporal confirmation and the interaction state machine come later.
Thresholds are provisional (see config.py) and come from one hand.
"""
from __future__ import annotations

from enum import Enum

from .. import config
from .feature_extractor import HandFeatures

OTHER_FINGERS = ("middle", "ring", "pinky")
FOUR_FINGERS = ("index", "middle", "ring", "pinky")


class Gesture(str, Enum):
    NONE = "none"            # no hand, bad data, or no rule matched
    POINT = "point"          # hover: index out, other fingers curled
    PINCH = "pinch"          # draw: thumb-index pinch active
    OPEN_PALM = "open_palm"  # pause
    FIST = "fist"            # command ready
    SHAKA = "shaka"          # eraser: thumb + pinky out, others curled


class FingerState(str, Enum):
    EXTENDED = "extended"
    CURLED = "curled"
    UNKNOWN = "unknown"      # in between: neither clearly extended nor curled


def finger_state(reach: float, pip_angle_deg: float) -> FingerState:
    if (reach >= config.FINGER_EXTENDED_MIN_REACH
            and pip_angle_deg >= config.FINGER_EXTENDED_MIN_ANGLE):
        return FingerState.EXTENDED
    if (reach <= config.FINGER_CURLED_MAX_REACH
            or pip_angle_deg <= config.FINGER_CURLED_MAX_ANGLE):
        return FingerState.CURLED
    return FingerState.UNKNOWN


def thumb_state(thumb_reach: float) -> FingerState:
    if thumb_reach >= config.THUMB_EXTENDED_MIN_REACH:
        return FingerState.EXTENDED
    if thumb_reach <= config.THUMB_TUCKED_MAX_REACH:
        return FingerState.CURLED
    return FingerState.UNKNOWN


def finger_states(f: HandFeatures) -> dict[str, FingerState]:
    states = {n: finger_state(f.reach[n], f.pip_angle_deg[n]) for n in FOUR_FINGERS}
    states["thumb"] = thumb_state(f.thumb_reach)
    return states


def classify(features: HandFeatures | None, pinch_active: bool) -> Gesture:
    """Classify one frame. `pinch_active` comes from the hysteresis PinchDetector.

    Priority: an active pinch wins over every other pose. Known ambiguity: in a
    real fist the thumb may rest against the index finger and look like a pinch.
    """
    if features is None:
        return Gesture.NONE
    if pinch_active:
        return Gesture.PINCH

    s = finger_states(features)
    others_curled = all(s[n] == FingerState.CURLED for n in OTHER_FINGERS)

    if s["index"] == FingerState.EXTENDED and others_curled:
        return Gesture.POINT
    if (s["thumb"] == FingerState.EXTENDED and s["pinky"] == FingerState.EXTENDED
            and all(s[n] == FingerState.CURLED for n in ("index", "middle", "ring"))):
        return Gesture.SHAKA
    if all(s[n] == FingerState.EXTENDED for n in FOUR_FINGERS) and s["thumb"] != FingerState.CURLED:
        return Gesture.OPEN_PALM
    if all(s[n] == FingerState.CURLED for n in FOUR_FINGERS):
        return Gesture.FIST
    return Gesture.NONE
