const video = document.getElementById("preview");
const overlayCanvas = document.getElementById("overlay");
const overlayToggle = document.getElementById("overlay-toggle");
const toggleBtn = document.getElementById("camera-toggle");
const statusEl = document.getElementById("camera-status");
const wsStatusEl = document.getElementById("ws-status");
const messageEl = document.getElementById("message");
const readoutEl = document.getElementById("readout");

let stream = null;
let loopId = null;
let lastResult = null;

const overlay = new HandOverlay(overlayCanvas);
const fps = new RateCounter(1000);
const latency = new RollingMean(30);
const serverMs = new RollingMean(30);

// Offscreen canvas used only to grab UNMIRRORED frames for the backend.
const captureCanvas = document.createElement("canvas");
captureCanvas.width = 640;
captureCanvas.height = 480;
const captureCtx = captureCanvas.getContext("2d");

const vision = new VisionClient({
  onStatus: (s) => {
    wsStatusEl.textContent = `Backend: ${s}`;
    const cls = s === "connected" ? "status--on"
              : s === "disconnected" ? "status--error" : "status--off";
    wsStatusEl.className = `status ${cls}`;
    if (s !== "connected") {       // never leave old landmarks on screen
      overlay.clear();
      lastResult = null;
    }
  },
  onResult: showResult,
  onError: (m) => { messageEl.textContent = `Backend error: ${m}`; },
});

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className = `status ${cls}`;
}

function showResult(r) {
  fps.tick();
  latency.add(performance.now() - r.captured_at_ms);
  serverMs.add(r.processing_ms);
  lastResult = r;
  overlay.draw(r.hand_detected ? r.landmarks : null); // no hand -> clears
  renderReadout();
}

function fmt(v, digits = 1) {
  return v === null ? "-" : v.toFixed(digits);
}

function renderReadout() {
  if (!lastResult) {
    readoutEl.textContent = "(no results yet)";
    return;
  }
  const r = lastResult;
  let text = `processed FPS: ${fps.perSecond().toFixed(1)}\n`;
  text += `hand detected: ${r.hand_detected}\n`;
  if (r.hand_detected) {
    const [x, y] = r.landmarks[8];
    text += `index tip raw: x=${x.toFixed(3)} y=${y.toFixed(3)}  (mirrored x=${(1 - x).toFixed(3)})\n`;
  } else {
    text += `index tip: -\n`;
  }
  text += `server processing (mean of last ${serverMs.values.length}): ${fmt(serverMs.mean())} ms\n`;
  text += `capture to result (mean, browser clock, incl. JPEG encode): ${fmt(latency.mean())} ms`;
  readoutEl.textContent = text;
}
setInterval(renderReadout, 500); // lets FPS visibly fall to 0 if results stop

function captureLoop() {
  loopId = requestAnimationFrame(captureLoop);
  if (!stream || video.readyState < 2) return;
  if (!vision.canSend()) return; // busy: skip, don't queue

  const capturedAt = performance.now();
  captureCtx.drawImage(video, 0, 0, 640, 480);
  const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.8);
  vision.sendFrame(dataUrl.slice(dataUrl.indexOf(",") + 1), capturedAt);
}

async function startCamera() {
  if (stream) return; // never open two streams
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    video.srcObject = stream;
    setStatus("Camera on", "status--on");
    toggleBtn.textContent = "Stop camera";
    messageEl.textContent = "Video stays on this computer. Nothing is uploaded.";
    stream.getVideoTracks()[0].addEventListener("ended", stopCamera);

    vision.connect();
    if (loopId === null) loopId = requestAnimationFrame(captureLoop);
  } catch (err) {
    stream = null;
    const reasons = {
      NotAllowedError: "Camera permission was denied. Allow it in your browser's site settings.",
      NotFoundError: "No camera found on this device.",
      NotReadableError: "Camera is in use by another application.",
    };
    messageEl.textContent = reasons[err.name] || `Camera error: ${err.message}`;
    setStatus("Camera error", "status--error");
  }
}

function stopCamera() {
  if (!stream) return;
  stream.getTracks().forEach((t) => t.stop()); // turns the camera light off
  stream = null;
  video.srcObject = null;

  if (loopId !== null) { cancelAnimationFrame(loopId); loopId = null; }
  vision.disconnect();

  overlay.clear();
  lastResult = null;
  fps.reset(); latency.reset(); serverMs.reset();
  setStatus("Camera off", "status--off");
  toggleBtn.textContent = "Start camera";
  renderReadout();
}

overlayToggle.addEventListener("change", () => {
  overlay.visible = overlayToggle.checked;
  if (!overlay.visible) overlay.clear();
});
toggleBtn.addEventListener("click", () => (stream ? stopCamera() : startCamera()));
