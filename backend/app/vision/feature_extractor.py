"""Geometric features from 21 hand landmarks.

Pure functions: no camera, no MediaPipe, no web server.
Input landmarks are normalised (0-1) and unmirrored, as MediaPipe reports them.
All distances are measured in PIXEL units (x scaled by width, y by height) and
then divided by hand scale, so features do not depend on camera distance.

Hand scale = distance from WRIST to MIDDLE_MCP. Known limitation: it shrinks
when the fingers point toward the camera, which inflates every ratio.
Only x and y are used. z is relative depth, not a physical distance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

NUM_LANDMARKS = 21
WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9
PINKY_MCP = 17

# name -> (MCP, PIP, DIP, TIP) landmark indices
FINGERS = {
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "pinky": (17, 18, 19, 20),
}

EPS = 1e-9
MIN_HAND_SCALE_PX = 10.0  # a hand smaller than this (in pixels) is unusable


@dataclass(frozen=True)
class HandFeatures:
    hand_scale_px: float
    pinch_ratio: float                 # thumb tip to index tip / hand scale
    reach: dict[str, float]            # finger tip to wrist / hand scale (higher = more extended)
    thumb_reach: float                 # thumb tip to pinky MCP / hand scale
    pip_angle_deg: dict[str, float]    # angle at the PIP joint (about 180 = straight)
    orientation_deg: float             # wrist->middle MCP direction; 0 = up, 90 = right (image)
    index_tip_rel: tuple[float, float] # (index tip - wrist) / hand scale


class _Degenerate(Exception):
    """Internal: a geometric quantity could not be computed."""


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle_deg(a, b, c) -> float:
    """Angle at b, in degrees, between the rays b->a and b->c."""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 < EPS or n2 < EPS:
        raise _Degenerate
    cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def extract_features(
    landmarks: Sequence[Sequence[float]] | None,
    frame_size: tuple[int, int] = (640, 480),
    min_scale_px: float = MIN_HAND_SCALE_PX,
) -> HandFeatures | None:
    """Return HandFeatures, or None if the input is unusable."""
    if landmarks is None or len(landmarks) != NUM_LANDMARKS:
        return None
    w, h = frame_size
    try:
        pts = [(float(p[0]) * w, float(p[1]) * h) for p in landmarks]
    except (TypeError, ValueError, IndexError):
        return None
    if not all(math.isfinite(c) for p in pts for c in p):
        return None

    scale = _dist(pts[WRIST], pts[MIDDLE_MCP])
    if scale < min_scale_px:
        return None

    try:
        reach = {n: _dist(pts[WRIST], pts[i[3]]) / scale for n, i in FINGERS.items()}
        angles = {n: _angle_deg(pts[i[0]], pts[i[1]], pts[i[2]]) for n, i in FINGERS.items()}
    except _Degenerate:
        return None

    dx = pts[MIDDLE_MCP][0] - pts[WRIST][0]
    dy = pts[MIDDLE_MCP][1] - pts[WRIST][1]
    tip = pts[INDEX_TIP]
    return HandFeatures(
        hand_scale_px=scale,
        pinch_ratio=_dist(pts[THUMB_TIP], pts[INDEX_TIP]) / (scale + EPS),
        reach=reach,
        thumb_reach=_dist(pts[THUMB_TIP], pts[PINKY_MCP]) / (scale + EPS),
        pip_angle_deg=angles,
        orientation_deg=math.degrees(math.atan2(dx, -dy)),
        index_tip_rel=((tip[0] - pts[WRIST][0]) / scale, (tip[1] - pts[WRIST][1]) / scale),
    )
