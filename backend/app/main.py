import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, APP_VERSION, FRONTEND_DIR, MODEL_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airink")

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "model_present": MODEL_PATH.exists(),
        "vision_engine_initialised": False,  # becomes real on Day 2
    }


# Mount the frontend LAST so /api routes take priority.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
