/* Small measurement helpers. Nothing here invents numbers:
   with no data, they report null / 0. */

/** Events per second over a sliding window (used for processed FPS). */
class RateCounter {
  constructor(windowMs = 1000) {
    this.windowMs = windowMs;
    this.times = [];
  }
  _trim(now) {
    while (this.times.length && now - this.times[0] > this.windowMs) this.times.shift();
  }
  tick(now = performance.now()) {
    this.times.push(now);
    this._trim(now);
  }
  perSecond(now = performance.now()) {
    this._trim(now);
    return (this.times.length * 1000) / this.windowMs;
  }
  reset() { this.times = []; }
}

/** Mean of the last N samples. Returns null when empty. */
class RollingMean {
  constructor(size = 30) {
    this.size = size;
    this.values = [];
  }
  add(v) {
    this.values.push(v);
    if (this.values.length > this.size) this.values.shift();
  }
  mean() {
    if (!this.values.length) return null;
    return this.values.reduce((a, b) => a + b, 0) / this.values.length;
  }
  reset() { this.values = []; }
}
