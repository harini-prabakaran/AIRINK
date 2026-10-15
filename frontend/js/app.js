const video = document.getElementById("preview");
const toggleBtn = document.getElementById("camera-toggle");
const statusEl = document.getElementById("camera-status");
const messageEl = document.getElementById("message");

let stream = null;

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className = `status ${cls}`;
}

async function startCamera() {
  if (stream) return; // guard: never open two streams
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    });
    video.srcObject = stream;
    setStatus("Camera on", "status--on");
    toggleBtn.textContent = "Stop camera";
    messageEl.textContent = "Video stays on this computer. Nothing is uploaded.";

    // If the camera is unplugged or taken away, shut down cleanly.
    stream.getVideoTracks()[0].addEventListener("ended", stopCamera);
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
  stream.getTracks().forEach((t) => t.stop()); // this turns the camera light off
  stream = null;
  video.srcObject = null;
  setStatus("Camera off", "status--off");
  toggleBtn.textContent = "Start camera";
}

toggleBtn.addEventListener("click", () => (stream ? stopCamera() : startCamera()));
