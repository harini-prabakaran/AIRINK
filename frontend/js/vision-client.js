/* WebSocket client for /ws/vision.
   Rules: at most ONE frame in flight; stale results are ignored. */
class VisionClient {
  constructor({ onResult, onStatus, onError }) {
    this.onResult = onResult;
    this.onStatus = onStatus;
    this.onError = onError;
    this.ws = null;
    this.seq = 0;               // next sequence number (never reset)
    this.lastAppliedSeq = -1;
    this.inFlight = false;
    this.sentAt = 0;
    this.wantOpen = false;
    this.reconnectTimer = null;
  }

  get isOpen() {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  connect() {
    this.wantOpen = true;
    // Never create two sockets.
    if (this.ws && (this.ws.readyState === WebSocket.OPEN ||
                    this.ws.readyState === WebSocket.CONNECTING)) return;

    const proto = location.protocol === "https:" ? "wss" : "ws";
    this.onStatus("connecting");
    const ws = new WebSocket(`${proto}://${location.host}/ws/vision`);
    this.ws = ws;

    ws.onopen = () => {
      this.inFlight = false;
      this.onStatus("connected");
    };
    ws.onmessage = (ev) => this._handle(ev.data);
    ws.onclose = () => {
      if (this.ws !== ws) return; // an older socket closing; ignore
      this.ws = null;
      this.inFlight = false;
      this.onStatus("disconnected");
      if (this.wantOpen) {
        this.reconnectTimer = setTimeout(() => this.connect(), 1000);
      }
    };
    ws.onerror = () => {}; // onclose always follows and handles it
  }

  disconnect() {
    this.wantOpen = false;
    clearTimeout(this.reconnectTimer);
    if (this.ws) this.ws.close();
  }

  /** True if we may send a new frame right now. Check BEFORE encoding a frame. */
  canSend() {
    if (!this.isOpen) return false;
    if (!this.inFlight) return true;
    if (performance.now() - this.sentAt > 2000) {
      console.warn("No reply for 2 s; releasing the in-flight slot");
      return true;
    }
    return false;
  }

  sendFrame(base64Jpeg, capturedAtMs) {
    this.inFlight = true;
    this.sentAt = performance.now();
    this.ws.send(JSON.stringify({
      type: "frame",
      seq: this.seq++,
      captured_at_ms: capturedAtMs,
      image: base64Jpeg,
    }));
  }

  _handle(data) {
    let msg;
    try { msg = JSON.parse(data); } catch { return; }

    // Only a reply to the most recently sent frame frees the slot.
    const isLatest = msg.seq === null || msg.seq === this.seq - 1;

    if (msg.type === "result") {
      if (isLatest) this.inFlight = false;
      if (msg.seq <= this.lastAppliedSeq) return; // stale: ignore
      this.lastAppliedSeq = msg.seq;
      this.onResult(msg);
    } else if (msg.type === "error") {
      if (isLatest) this.inFlight = false;
      this.onError(msg.message);
    }
  }
}
