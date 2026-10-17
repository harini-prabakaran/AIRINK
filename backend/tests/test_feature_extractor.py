import math

import pytest

from backend.app.vision.feature_extractor import HandFeatures, extract_features

# Real landmarks from the developer's own open-palm photo (Day 1).
OPEN_HAND = [
    (0.483, 0.768, 0.000), (0.431, 0.759, -0.027), (0.381, 0.725, -0.046),
    (0.339, 0.687, -0.063), (0.302, 0.667, -0.081),
    (0.389, 0.602, -0.030), (0.351, 0.537, -0.051), (0.328, 0.495, -0.068), (0.309, 0.455, -0.081),
    (0.418, 0.572, -0.031), (0.389, 0.492, -0.049), (0.370, 0.438, -0.064), (0.352, 0.394, -0.075),
    (0.452, 0.566, -0.036), (0.430, 0.488, -0.055), (0.413, 0.435, -0.070), (0.396, 0.391, -0.080),
    (0.490, 0.576, -0.043), (0.496, 0.511, -0.059), (0.498, 0.467, -0.068), (0.497, 0.426, -0.076),
]
FINGERS = ("index", "middle", "ring", "pinky")
TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
MCPS = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}


def transformed(hand, s, ax, ay):
    """Uniformly scale and shift a hand (same factor on both normalised axes)."""
    return [(x * s + ax, y * s + ay, z) for x, y, z in hand]


def test_open_hand_features_are_sane():
    f = extract_features(OPEN_HAND)
    assert isinstance(f, HandFeatures)
    assert f.pinch_ratio > 0.8                       # thumb far from index
    for name in FINGERS:
        assert f.reach[name] > 1.4                   # fingers extended
        assert f.pip_angle_deg[name] > 160           # nearly straight


def test_hand_scale_is_measured_in_pixels_not_normalised_units():
    expected = math.hypot((0.418 - 0.483) * 640, (0.572 - 0.768) * 480)
    assert extract_features(OPEN_HAND).hand_scale_px == pytest.approx(expected)


def test_touching_fingertips_give_zero_pinch_ratio():
    pinched = list(OPEN_HAND)
    pinched[4] = OPEN_HAND[8]
    assert extract_features(pinched).pinch_ratio == pytest.approx(0.0, abs=1e-9)


def test_nearly_touching_fingertips_give_small_ratio():
    pinched = list(OPEN_HAND)
    pinched[4] = (OPEN_HAND[8][0] + 0.005, OPEN_HAND[8][1] + 0.005, 0.0)
    assert extract_features(pinched).pinch_ratio < 0.1


def test_features_do_not_depend_on_hand_size_or_position():
    a = extract_features(OPEN_HAND)
    b = extract_features(transformed(OPEN_HAND, 0.5, 0.2, 0.1))
    assert b.hand_scale_px == pytest.approx(a.hand_scale_px * 0.5, rel=1e-6)
    assert b.pinch_ratio == pytest.approx(a.pinch_ratio, rel=1e-6)
    for name in FINGERS:
        assert b.reach[name] == pytest.approx(a.reach[name], rel=1e-6)


def test_curled_fingers_have_lower_reach_than_open_fingers():
    fist = list(OPEN_HAND)
    wrist = OPEN_HAND[0]
    for name in FINGERS:
        mcp = OPEN_HAND[MCPS[name]]
        fist[TIPS[name]] = (mcp[0] + 0.3 * (wrist[0] - mcp[0]),
                            mcp[1] + 0.3 * (wrist[1] - mcp[1]), 0.0)
    open_f, fist_f = extract_features(OPEN_HAND), extract_features(fist)
    for name in FINGERS:
        assert fist_f.reach[name] < open_f.reach[name]
        assert fist_f.reach[name] < 1.2


def test_orientation_up_is_zero_and_right_is_ninety():
    up = list(OPEN_HAND)
    up[9] = (OPEN_HAND[0][0], OPEN_HAND[0][1] - 0.2, 0.0)
    right = list(OPEN_HAND)
    right[9] = (OPEN_HAND[0][0] + 0.2, OPEN_HAND[0][1], 0.0)
    assert extract_features(up).orientation_deg == pytest.approx(0.0, abs=1e-6)
    assert extract_features(right).orientation_deg == pytest.approx(90.0, abs=1e-6)


def test_hand_too_small_is_rejected():
    assert extract_features(transformed(OPEN_HAND, 0.01, 0.4, 0.4)) is None


NAN_HAND = list(OPEN_HAND)
NAN_HAND[8] = (float("nan"), 0.4, 0.0)
INF_HAND = list(OPEN_HAND)
INF_HAND[8] = (float("inf"), 0.4, 0.0)


@pytest.mark.parametrize(
    "bad",
    [None, [], OPEN_HAND[:20], NAN_HAND, INF_HAND, [(0.5, 0.5, 0.0)] * 21],
    ids=["none", "empty", "twenty-points", "nan", "inf", "all-identical"],
)
def test_invalid_input_returns_none(bad):
    assert extract_features(bad) is None
