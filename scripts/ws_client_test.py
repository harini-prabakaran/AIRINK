"""Day 2, Step 2: test /ws/vision from Python, with no browser involved."""
import asyncio
import base64
import json
import sys
import time
from pathlib import Path

import cv2
import websockets

URL = "ws://localhost:8000/ws/vision"
REPO_ROOT = Path(__file__).resolve().parents[1]


def frame_msg(seq: int, b64: str) -> str:
    return json.dumps({"type": "frame", "seq": seq,
                       "captured_at_ms": time.time() * 1000, "image": b64})


async def main(path: str) -> None:
    bgr = cv2.imread(path)
    if bgr is None:
        sys.exit(f"Could not read {path}")
    bgr = cv2.resize(bgr, (640, 480))
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
    b64 = base64.b64encode(buf.tobytes()).decode()
    print(f"JPEG size: {len(buf) / 1024:.1f} KB (base64: {len(b64) / 1024:.1f} KB)\n")

    async with websockets.connect(URL) as ws:
        print("--- 5 valid frames ---")
        for seq in range(5):
            sent = time.perf_counter()
            await ws.send(frame_msg(seq, b64))
            reply = json.loads(await ws.recv())
            round_trip = (time.perf_counter() - sent) * 1000
            if reply["type"] == "result":
                print(f"seq {reply['seq']}: hand={reply['hand_detected']} "
                      f"server={reply['processing_ms']} ms  round-trip={round_trip:.1f} ms")
            else:
                print("unexpected:", reply)

        print("\n--- bad messages (connection must survive) ---")
        await ws.send("this is not json")
        print("not json      ->", json.loads(await ws.recv()))

        await ws.send(frame_msg(98, "!!!not-base64!!!"))
        print("bad base64    ->", json.loads(await ws.recv()))

        await ws.send(frame_msg(99, base64.b64encode(b"not a jpeg").decode()))
        print("not a JPEG    ->", json.loads(await ws.recv()))

        print("\n--- still alive? ---")
        await ws.send(frame_msg(100, b64))
        reply = json.loads(await ws.recv())
        print(f"seq {reply['seq']}: type={reply['type']} hand={reply.get('hand_detected')}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1
                     else str(REPO_ROOT / "experiments/data/test_hand.jpg")))
