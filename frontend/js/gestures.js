/* TEMPORARY air-input layer (Day 3).
   The pinch rule below is deliberately naive: a single threshold, no hysteresis,
   no temporal confirmation. On Day 4 it is replaced by the backend gesture engine. */
const FRAME_W = 640;   // capture size; needed to undo the x/y normalisation difference
const FRAME_H = 480;
const LM_WRIST = 0, LM_THUMB_TIP = 4, LM_INDEX_TIP = 8, LM_MIDDLE_MCP = 9;

const ACTIVE_MARGIN = 0.15;    // ignore the outer 15% of the camera frame on each side
const PINCH_THRESHOLD = 0.30;  // pinch ratio below this = draw (tune from your own readout)
const MAX_JUMP = 250;          // logical px; a bigger one-frame jump breaks the stroke

const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

/** The ONLY place camera coordinates become canvas coordinates.
    Applies mirroring (1 - x), the active region, and clamping. */
function mapToCanvas(xRaw, yRaw) {
  const span = 1 - 2 * ACTIVE_MARGIN;
  const nx = clamp(((1 - xRaw) - ACTIVE_MARGIN) / span, 0, 1);
  const ny = clamp((yRaw - ACTIVE_MARGIN) / span, 0, 1);
  return { x: nx * LOGICAL_W, y: ny * LOGICAL_H };
}

/** Distance in camera-pixel units, so x and y are comparable. */
function pixelDist(a, b) {
  return Math.hypot((a[0] - b[0]) * FRAME_W, (a[1] - b[1]) * FRAME_H);
}

/** thumb-index distance / hand size. Dimensionless; null if the hand size is unusable. */
function pinchRatio(lm) {
  const scale = pixelDist(lm[LM_WRIST], lm[LM_MIDDLE_MCP]);
  if (!Number.isFinite(scale) || scale < 1e-6) return null;
  const ratio = pixelDist(lm[LM_THUMB_TIP], lm[LM_INDEX_TIP]) / scale;
  return Number.isFinite(ratio) ? ratio : null;
}

class AirInput {
  constructor(engine, cursorEl) {
    this.engine = engine;
    this.cursor = cursorEl;
    this.active = false;     // true only while an AIR stroke is in progress
    this.last = null;
    this.lastRatio = null;
    this.endReasons = { pinch: 0, handLost: 0, jump: 0 };
    this.lastReleaseRatio = null;
  }

  update(result) {
    if (!result.hand_detected || !result.landmarks || result.landmarks.length !== 21) {
      if (this.active) this.endReasons.handLost++;
      this.release();
      return;
    }
    const lm = result.landmarks;
    const { x, y } = mapToCanvas(lm[LM_INDEX_TIP][0], lm[LM_INDEX_TIP][1]);
    this.lastRatio = pinchRatio(lm);
    this._showCursor(x, y);

    const pinching = this.lastRatio !== null && this.lastRatio < PINCH_THRESHOLD;

    if (pinching) {
      if (!this.active) {
        if (this.engine.isDrawing) return;      // the mouse is mid-stroke; don't interfere
        this.engine.beginStroke(x, y);
        this.active = true;
      } else if (Math.hypot(x - this.last.x, y - this.last.y) > MAX_JUMP) {
        this.endReasons.jump++;
        this.engine.endStroke();                // discontinuity: never draw across it
        this.engine.beginStroke(x, y);
      } else {
        this.engine.addPoint(x, y);
      }
      this.last = { x, y };
    } else if (this.active) {
      this.endReasons.pinch++;
      this.lastReleaseRatio = this.lastRatio;
      this._endStroke();
    }
    this.cursor.classList.toggle("is-drawing", this.active);
  }

  /** Hand lost, backend gone, or camera stopped: finish safely and hide the cursor. */
  release() {
    if (this.active) this._endStroke();
    this.lastRatio = null;
    this.cursor.classList.remove("is-visible", "is-drawing");
  }

  _endStroke() {
    this.engine.endStroke();
    this.active = false;
    this.last = null;
  }

  _showCursor(x, y) {
    this.cursor.style.left = `${(x / LOGICAL_W) * 100}%`;
    this.cursor.style.top = `${(y / LOGICAL_H) * 100}%`;
    this.cursor.classList.add("is-visible");
  }
}
