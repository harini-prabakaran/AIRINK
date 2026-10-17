"""WebSocket integration tests with a FAKE tracker: no camera, no MediaPipe needed."""
import asyncio
import base64
import json
from types import SimpleNamespace

import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.vision_ws import router
from backend.tests.hands import build_hand


def jpeg_b64() -> str:
    ok, buf = cv2.imencode(".jpg", np.zeros((480, 640, 3), dtype=np.uint8))
    assert ok
    return base64.b64encode(buf.tobytes()).decode()


def frame(seq: int, image: str | None = None) -> str:
    return json.dumps({"type": "frame", "seq": seq, "captured_at_ms": 1.0,
                       "image": image or jpeg_b64()})


class FakeTracker:
    """Returns scripted results; None in the script means 'no hand'."""

    def __init__(self, script):
        self.script = list(script)

    def process(self, rgb, timestamp_ms):
        hand = self.script.pop(0)
        if hand is None:
            return SimpleNamespace(hand_detected=False, landmarks=[], handedness_score=None)
        return SimpleNamespace(hand_detected=True, landmarks=hand, handedness_score=0.9)


def make_client(tracker):
    app = FastAPI()
    app.include_router(router)
    app.state.tracker = tracker
    app.state.tracker_lock = asyncio.Lock()
    return TestClient(app)


def test_result_carries_raw_gesture_and_features():
    client = make_client(FakeTracker([build_hand()]))
    with client.websocket_connect("/ws/vision") as ws:
        ws.send_text(frame(0))
        msg = ws.receive_json()
    assert msg["type"] == "result" and msg["seq"] == 0
    assert msg["hand_detected"] is True
    assert msg["raw_gesture"] == "open_palm"
    assert msg["features"]["finger_states"]["thumb"] == "extended"


def test_no_hand_result_has_no_features():
    client = make_client(FakeTracker([None]))
    with client.websocket_connect("/ws/vision") as ws:
        ws.send_text(frame(0))
        msg = ws.receive_json()
    assert msg["hand_detected"] is False
    assert msg["raw_gesture"] == "none"
    assert msg["features"] is None
    assert msg["pinch_active"] is False


def test_pinch_state_does_not_survive_tracking_loss_over_the_socket():
    pinched = build_hand(index=True, middle=False, ring=False, pinky=False, thumb=False, pinch=True)
    band = build_hand(index=True, middle=False, ring=False, pinky=False, thumb=False)
    ix, iy, _ = band[8]
    band[4] = (ix + 35 / 640, iy, 0.0)  # ratio about 0.35: inside the hysteresis band
    client = make_client(FakeTracker([pinched, None, band]))
    with client.websocket_connect("/ws/vision") as ws:
        replies = []
        for seq in range(3):
            ws.send_text(frame(seq))
            replies.append(ws.receive_json())
    assert [r["pinch_active"] for r in replies] == [True, False, False]


def test_malformed_messages_get_errors_and_connection_survives():
    client = make_client(FakeTracker([build_hand()]))
    with client.websocket_connect("/ws/vision") as ws:
        ws.send_text("not json")
        assert ws.receive_json()["type"] == "error"
        ws.send_text(frame(1, image="!!!not-base64!!!"))
        assert ws.receive_json()["type"] == "error"
        ws.send_text(frame(2))
        assert ws.receive_json()["type"] == "result"


def test_missing_tracker_is_reported_and_closed():
    client = make_client(None)
    with client.websocket_connect("/ws/vision") as ws:
        assert ws.receive_json()["type"] == "error"
