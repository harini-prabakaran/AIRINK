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
