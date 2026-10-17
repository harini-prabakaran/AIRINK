/* Drawing engine. Knows nothing about cameras or gestures.
   Strokes are stored as data: { color, size, points: [{x, y}] }
   in LOGICAL coordinates (1280 x 720), independent of screen size. */
const LOGICAL_W = 1280;
const LOGICAL_H = 720;
const EXPORT_BACKGROUND = "#0f1218";

class DrawingEngine {
  constructor(committedCanvas, liveCanvas) {
    this.committed = committedCanvas;
    this.live = liveCanvas;
    this.cctx = committedCanvas.getContext("2d");
    this.lctx = liveCanvas.getContext("2d");

    this.strokes = [];     // finished strokes
    this.redoStack = [];   // strokes removed by undo
    this.current = null;   // stroke being drawn, or null
    this.color = "#22d3ee";
    this.size = 6;
    this.onChange = null;  // called whenever stroke lists change

    this._setupResolution();
  }

  _notify() { if (this.onChange) this.onChange(); }

  _setupResolution() {
    const dpr = window.devicePixelRatio || 1;
    for (const [canvas, ctx] of [[this.committed, this.cctx], [this.live, this.lctx]]) {
      canvas.width = Math.round(LOGICAL_W * dpr);
      canvas.height = Math.round(LOGICAL_H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
  }

  toLogical(clientX, clientY) {
    const rect = this.live.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * LOGICAL_W;
    const y = ((clientY - rect.top) / rect.height) * LOGICAL_H;
    return {
      x: Math.min(Math.max(x, 0), LOGICAL_W),
      y: Math.min(Math.max(y, 0), LOGICAL_H),
    };
  }

  get isDrawing() { return this.current !== null; }
  get canUndo() { return this.strokes.length > 0 && !this.isDrawing; }
  get canRedo() { return this.redoStack.length > 0 && !this.isDrawing; }

  beginStroke(x, y) {
    if (this.current) this.endStroke(); // never leave a stroke dangling
    this.current = { color: this.color, size: this.size, points: [{ x, y }] };
    this._renderLive();
  }

  addPoint(x, y) {
    if (!this.current) return;
    const last = this.current.points[this.current.points.length - 1];
    if (last.x === x && last.y === y) return;
    this.current.points.push({ x, y });
    this._renderLive();
  }

  endStroke() {
    if (!this.current) return;
    this.strokes.push(this.current);
    this.redoStack = []; // drawing something new discards the "future"
    this._drawStroke(this.cctx, this.current);
    this.current = null;
    this.lctx.clearRect(0, 0, LOGICAL_W, LOGICAL_H);
    this._notify();
  }

  undo() {
    if (!this.canUndo) return false;
    this.redoStack.push(this.strokes.pop());
    this.redrawAll();
    this._notify();
    return true;
  }

  redo() {
    if (!this.canRedo) return false;
    this.strokes.push(this.redoStack.pop());
    this.redrawAll();
    this._notify();
    return true;
  }

  /** Not undoable: the UI must ask for confirmation before calling this. */
  clear() {
    if (this.current) this.endStroke();
    this.strokes = [];
    this.redoStack = [];
    this.redrawAll();
    this._notify();
  }

  /** Resolves to a PNG Blob: committed strokes on an opaque background. */
  exportPNG() {
    const out = document.createElement("canvas");
    out.width = this.committed.width;
    out.height = this.committed.height;
    const ctx = out.getContext("2d");
    ctx.fillStyle = EXPORT_BACKGROUND;
    ctx.fillRect(0, 0, out.width, out.height);
    ctx.drawImage(this.committed, 0, 0);
    return new Promise((resolve, reject) =>
      out.toBlob((b) => (b ? resolve(b) : reject(new Error("Export failed"))), "image/png"));
  }

  redrawAll() {
    this.cctx.clearRect(0, 0, LOGICAL_W, LOGICAL_H);
    for (const s of this.strokes) this._drawStroke(this.cctx, s);
  }

  _renderLive() {
    this.lctx.clearRect(0, 0, LOGICAL_W, LOGICAL_H);
    if (this.current) this._drawStroke(this.lctx, this.current);
  }

  _drawStroke(ctx, stroke) {
    const p = stroke.points;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = stroke.color;
    ctx.fillStyle = stroke.color;
    ctx.lineWidth = stroke.size;

    if (p.length === 1) {
      ctx.beginPath();
      ctx.arc(p[0].x, p[0].y, stroke.size / 2, 0, Math.PI * 2);
      ctx.fill();
      return;
    }

    ctx.beginPath();
    ctx.moveTo(p[0].x, p[0].y);
    for (let i = 1; i < p.length - 1; i++) {
      const midX = (p[i].x + p[i + 1].x) / 2;
      const midY = (p[i].y + p[i + 1].y) / 2;
      ctx.quadraticCurveTo(p[i].x, p[i].y, midX, midY);
    }
    ctx.lineTo(p[p.length - 1].x, p[p.length - 1].y);
    ctx.stroke();
  }
}
