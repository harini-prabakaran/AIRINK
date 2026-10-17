"""Central configuration. Tunable settings live here, not scattered in code."""
from pathlib import Path

APP_NAME = "AIRINK"
APP_VERSION = "0.1.0"

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "frontend"
MODEL_PATH = REPO_ROOT / "models" / "hand_landmarker.task"

# WebSocket limits
MAX_FRAME_BYTES = 500_000       # decoded JPEG size
MAX_MESSAGE_CHARS = 700_000     # raw message size (base64 is ~4/3 larger)

# Pinch hysteresis (provisional: from one hand, to be re-checked with more data)
# pinch_ratio = thumb-tip to index-tip distance / hand scale
PINCH_ENTER_BELOW = 0.25   # start drawing when the ratio falls below this
PINCH_EXIT_ABOVE = 0.45    # stop drawing only when the ratio rises above this

# Finger-state thresholds (provisional: derived from ONE hand; re-check with more data)
# reach = fingertip-to-wrist distance / hand scale; pip angle in degrees (180 = straight)
FINGER_EXTENDED_MIN_REACH = 1.45
FINGER_EXTENDED_MIN_ANGLE = 165.0
FINGER_CURLED_MAX_REACH = 1.20
FINGER_CURLED_MAX_ANGLE = 110.0
# thumb_reach = thumb tip to pinky MCP / hand scale
THUMB_EXTENDED_MIN_REACH = 1.10
THUMB_TUCKED_MAX_REACH = 0.80
