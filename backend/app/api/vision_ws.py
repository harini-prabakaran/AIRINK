"""WebSocket endpoint: receives JPEG frames, returns hand landmarks.

api/ moves data. All hand logic lives in vision/.
"""
import asyncio
import base64
import binascii
import logging
import time
from typing import Literal

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from ..config import MAX_FRAME_BYTES, MAX_MESSAGE_CHARS

router = APIRouter()
logger = logging.getLogger("airink.ws")


class FrameMessage(BaseModel):
    type: Literal["frame"]
    seq: int = Field(ge=0)
    captured_at_ms: float  # browser clock; echoed back, never compared to server clock
    image: str             # base64-encoded JPEG


def decode_jpeg(b64: str) -> np.ndarray:
    """base64 JPEG -> RGB array. Raises ValueError with a safe message."""
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Image is not valid base64.")
    if len(raw) > MAX_FRAME_BYTES:
        raise ValueError("Frame is too large.")
    bgr = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Image could not be decoded.")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def error_reply(message: str, seq: int | None = None) -> dict:
    return {"type": "error", "seq": seq, "message": message}


@router.websocket("/ws/vision")
async def vision_socket(ws: WebSocket) -> None:
    await ws.accept()
    tracker = ws.app.state.tracker
    lock: asyncio.Lock = ws.app.state.tracker_lock

    if tracker is None:
        await ws.send_json(error_reply("Vision engine unavailable (model missing?)."))
        await ws.close(code=1011)
        return

    logger.info("Client connected")
    try:
        while True:
            text = await ws.receive_text()

            if len(text) > MAX_MESSAGE_CHARS:
                await ws.send_json(error_reply("Message too large."))
                continue

            try:
                msg = FrameMessage.model_validate_json(text)
            except ValidationError:
                await ws.send_json(error_reply("Invalid message format."))
                continue

            started = time.perf_counter()
            try:
                rgb = decode_jpeg(msg.image)
                async with lock:
                    result = await asyncio.to_thread(
                        tracker.process, rgb, int(time.monotonic() * 1000)
                    )
            except ValueError as exc:  # expected, safe to show
                await ws.send_json(error_reply(str(exc), msg.seq))
                continue
            except Exception:  # unexpected: log details, hide them from the client
                logger.exception("Inference failed for seq %d", msg.seq)
                await ws.send_json(error_reply("Internal vision error.", msg.seq))
                continue

            await ws.send_json({
                "type": "result",
                "seq": msg.seq,
                "captured_at_ms": msg.captured_at_ms,
                "processing_ms": round((time.perf_counter() - started) * 1000, 2),
                "hand_detected": result.hand_detected,
                "landmarks": [[round(c, 5) for c in lm] for lm in result.landmarks],
                "handedness_score": result.handedness_score,
            })
    except WebSocketDisconnect:
        logger.info("Client disconnected")
