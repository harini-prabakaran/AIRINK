/* Draws the hand skeleton on a transparent canvas above the video. */
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],            // thumb
  [0, 5], [5, 6], [6, 7], [7, 8],            // index
  [5, 9], [9, 10], [10, 11], [11, 12],       // middle
  [9, 13], [13, 14], [14, 15], [15, 16],     // ring
  [13, 17], [17, 18], [18, 19], [19, 20],    // pinky
  [0, 17],                                   // palm edge
];
const INDEX_TIP = 8;

class HandOverlay {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.visible = true;
    const css = getComputedStyle(document.documentElement);
    this.boneColor = css.getPropertyValue("--cyan").trim() || "#22d3ee";
    this.jointColor = css.getPropertyValue("--violet").trim() || "#a78bfa";
  }

  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /** THE one place mirroring is applied. Raw x is unmirrored; the video is
      CSS-mirrored, so the displayed x is (1 - x). y is not flipped. */
  toDisplay(x, y) {
    return [(1- x) * this.canvas.width, y * this.canvas.height];
  }

  /** Draw a fresh set of 21 landmarks, or clear if given none. */
  draw(landmarks) {
    this.clear();
    if (!this.visible || !landmarks || landmarks.length !== 21) return;
    const ctx = this.ctx;
    const pts = landmarks.map(([x, y]) => this.toDisplay(x, y));

    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.strokeStyle = this.boneColor;
    ctx.beginPath();
    for (const [a, b] of HAND_CONNECTIONS) {
      ctx.moveTo(pts[a][0], pts[a][1]);
      ctx.lineTo(pts[b][0], pts[b][1]);
    }
    ctx.stroke();

    ctx.fillStyle = this.jointColor;
    for (const [px, py] of pts) {
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Index fingertip marker: this will become the drawing cursor.
    const [tx, ty] = pts[INDEX_TIP];
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(tx, ty, 10, 0, Math.PI * 2);
    ctx.stroke();
  }
}
