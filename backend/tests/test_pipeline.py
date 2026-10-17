from backend.app.vision.gesture_classifier import Gesture
from backend.app.vision.pipeline import GesturePipeline
from backend.tests.hands import H, W, build_hand

SIZE = (W, H)


def pinched():
    return build_hand(index=True, middle=False, ring=False, pinky=False, thumb=False, pinch=True)


def in_hysteresis_band():
    """Thumb tip near the index tip: ratio between the enter (0.25) and exit (0.45) thresholds."""
    hand = build_hand(index=True, middle=False, ring=False, pinky=False, thumb=False)
    ix, iy, _ = hand[8]
    hand[4] = (ix + 35 / W, iy, 0.0)          # 35 px away, hand scale is 100 px -> ratio 0.35
    return hand


def test_open_palm_end_to_end():
    out = GesturePipeline().process(build_hand(), SIZE)
    assert out.gesture == Gesture.OPEN_PALM
    assert out.pinch_active is False
    assert out.features is not None


def test_no_hand_gives_none_and_no_features():
    out = GesturePipeline().process(None, SIZE)
    assert out.gesture == Gesture.NONE
    assert out.features is None and out.finger_states is None
    assert out.pinch_active is False


def test_pinch_survives_the_hysteresis_band():
    p = GesturePipeline()
    assert p.process(pinched(), SIZE).pinch_active is True
    assert p.process(in_hysteresis_band(), SIZE).pinch_active is True   # still held


def test_band_alone_does_not_start_a_pinch():
    assert GesturePipeline().process(in_hysteresis_band(), SIZE).pinch_active is False


def test_tracking_loss_resets_the_pinch():
    p = GesturePipeline()
    p.process(pinched(), SIZE)
    p.process(None, SIZE)                                               # hand lost
    # the hand returns inside the band: must NOT resume the old pinch
    assert p.process(in_hysteresis_band(), SIZE).pinch_active is False


def test_unusable_landmarks_also_reset_the_pinch():
    p = GesturePipeline()
    p.process(pinched(), SIZE)
    bad = pinched()
    bad[8] = (float("nan"), 0.5, 0.0)
    assert p.process(bad, SIZE).pinch_active is False
    assert p.process(in_hysteresis_band(), SIZE).pinch_active is False


def test_to_wire_is_json_serialisable_and_labelled_raw():
    import json
    wire = GesturePipeline().process(build_hand(), SIZE).to_wire()
    json.dumps(wire)
    assert wire["raw_gesture"] == "open_palm"
    assert set(wire["features"]["finger_states"]) == {"index", "middle", "ring", "pinky", "thumb"}


def test_to_wire_without_hand():
    wire = GesturePipeline().process(None, SIZE).to_wire()
    assert wire == {"raw_gesture": "none", "pinch_active": False, "features": None}
