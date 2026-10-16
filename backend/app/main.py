import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.vision_ws import router as vision_router
from .config import APP_NAME, APP_VERSION, FRONTEND_DIR, MODEL_PATH
from .vision.hand_tracker import HandTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airink")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create the tracker ONCE.
    app.state.tracker = None
    app.state.tracker_lock = asyncio.Lock()
    if MODEL_PATH.exists():
        try:
            app.state.tracker = HandTracker(MODEL_PATH)
        except Exception:
            logger.exception("Failed to initialise HandTracker")
    else:
        logger.warning("Model not found at %s", MODEL_PATH)
    yield
    # Shutdown: release resources.
    if app.state.tracker is not None:
        app.state.tracker.close()


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.include_router(vision_router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "model_present": MODEL_PATH.exists(),
        "vision_engine_initialised": app.state.tracker is not None,
    }


# Mount the frontend LAST so /api and /ws routes take priority.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
