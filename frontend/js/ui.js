/* Connects the toolbar and mouse/touch to the DrawingEngine. */
const engine = new DrawingEngine(
  document.getElementById("draw-canvas"),
  document.getElementById("draw-live"),
);
const liveCanvas = document.getElementById("draw-live");
const strokeCountEl = document.getElementById("stroke-count");
const sizeInput = document.getElementById("brush-size");
const sizeLabel = document.getElementById("brush-size-label");
const swatches = document.querySelectorAll(".swatch");

function updateStrokeCount() {
  strokeCountEl.textContent = `Strokes: ${engine.strokes.length}`;
}

// --- Pointer (mouse / touch / pen) ---
liveCanvas.addEventListener("pointerdown", (ev) => {
  liveCanvas.setPointerCapture(ev.pointerId); // keep receiving events if the pointer leaves
  const { x, y } = engine.toLogical(ev.clientX, ev.clientY);
  engine.beginStroke(x, y);
});
liveCanvas.addEventListener("pointermove", (ev) => {
  if (!engine.isDrawing) return;
  const { x, y } = engine.toLogical(ev.clientX, ev.clientY);
  engine.addPoint(x, y);
});
function finishStroke() {
  engine.endStroke();
  updateStrokeCount();
}
liveCanvas.addEventListener("pointerup", finishStroke);
liveCanvas.addEventListener("pointercancel", finishStroke);

// --- Colour swatches ---
swatches.forEach((btn) => {
  btn.style.setProperty("--c", btn.dataset.color);
  btn.addEventListener("click", () => {
    engine.color = btn.dataset.color;
    swatches.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  });
});

// --- Brush size ---
sizeInput.addEventListener("input", () => {
  engine.size = Number(sizeInput.value);
  sizeLabel.textContent = `${engine.size} px`;
});

updateStrokeCount();

/* --- Day 3, Step 2: history, clear, export --- */
const undoBtn = document.getElementById("undo-btn");
const redoBtn = document.getElementById("redo-btn");
const clearBtn = document.getElementById("clear-btn");
const exportBtn = document.getElementById("export-btn");

function refreshControls() {
  updateStrokeCount();
  undoBtn.disabled = !engine.canUndo;
  redoBtn.disabled = !engine.canRedo;
  clearBtn.disabled = engine.strokes.length === 0;
  exportBtn.disabled = engine.strokes.length === 0;
}
engine.onChange = refreshControls;

undoBtn.addEventListener("click", () => engine.undo());
redoBtn.addEventListener("click", () => engine.redo());

clearBtn.addEventListener("click", () => {
  if (confirm("Clear the whole canvas? This cannot be undone.")) engine.clear();
});

exportBtn.addEventListener("click", async () => {
  try {
    const blob = await engine.exportPNG();
    const url = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 19);
    const a = document.createElement("a");
    a.href = url;
    a.download = `airink-${stamp}.png`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Could not export the image.");
    console.error(err);
  }
});

document.addEventListener("keydown", (ev) => {
  const t = ev.target;
  if (t instanceof HTMLTextAreaElement || (t instanceof HTMLInputElement && t.type === "text")) return;
  if (!(ev.metaKey || ev.ctrlKey) || ev.key.toLowerCase() !== "z") return;
  ev.preventDefault();
  if (ev.shiftKey) engine.redo(); else engine.undo();
});

refreshControls();

/* --- Day 3, Step 3: air input --- */
const airInput = new AirInput(engine, document.getElementById("air-cursor"));
