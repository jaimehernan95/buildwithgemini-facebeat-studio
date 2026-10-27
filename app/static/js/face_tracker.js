/**
 * face_tracker.js - MediaPipe Face Mesh & Facial Expression Classifier.
 * Features WebGL capability probing, graceful CPU/Virtual fallback on WebGL context failure,
 * keyboard controls, manual triggers, and Auto-Groove testing mode.
 */
class FaceTracker {
  constructor(videoElement, onResultsCallback, onStatusChange) {
    this.videoElement = videoElement;
    this.onResultsCallback = onResultsCallback;
    this.onStatusChange = onStatusChange;

    this.faceMesh = null;
    this.isProcessingFrame = false;
    this.webglDisabled = false;
    this.webglSupported = true;
    this.consecutiveFailures = 0;

    // Current normalized expression scores (0.0 to 1.0)
    this.expressions = {
      jawOpen: 0.0,
      smile: 0.0,
      browRaise: 0.0,
    };

    // Calibration baseline (resting face)
    this.baseline = {
      jawOpen: 0.04,
      smile: 0.42,
      browRaise: 0.12,
    };

    this.isCalibrating = false;
    this.calibrationFrames = [];
    this.lastLandmarks = null;
    this.triggerTimeouts = {};

    this.autoGroove = false;
    this.autoGrooveInterval = null;

    this.initKeyboardListeners();
  }

  static isWebGLSupported() {
    try {
      const canvas = document.createElement("canvas");
      canvas.width = 1;
      canvas.height = 1;
      const gl =
        canvas.getContext("webgl2") ||
        canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl");
      if (!gl) return false;
      if (typeof gl.isContextLost === "function" && gl.isContextLost()) return false;
      return true;
    } catch (e) {
      return false;
    }
  }

  async initialize() {
    this.webglSupported = FaceTracker.isWebGLSupported();

    if (!this.webglSupported) {
      console.warn("[FaceTracker] WebGL context unavailable in this environment. Running on CPU Virtual Mode.");
      this.webglDisabled = true;
      if (this.onStatusChange) {
        this.onStatusChange({
          webgl: false,
          mode: "cpu_virtual",
          message: "WebGL unavailable - CPU Virtual Mode active (use keys or buttons)",
        });
      }
      return;
    }

    if (typeof FaceMesh === "undefined") {
      console.warn("[FaceTracker] MediaPipe FaceMesh library not loaded. Running in fallback mode.");
      this.webglDisabled = true;
      return;
    }

    try {
      this.faceMesh = new FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
      });

      this.faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      this.faceMesh.onResults((results) => this.processResults(results));

      this.startFramePump();
      console.log("[FaceTracker] MediaPipe FaceMesh tracker initialized with WebGL acceleration.");
      if (this.onStatusChange) {
        this.onStatusChange({
          webgl: true,
          mode: "hardware_webgl",
          message: "WebGL Hardware Accelerated Face Tracking",
        });
      }
    } catch (e) {
      console.warn("[FaceTracker] MediaPipe initialization error:", e);
      this.webglDisabled = true;
      if (this.onStatusChange) {
        this.onStatusChange({
          webgl: false,
          mode: "cpu_virtual",
          message: "WebGL init failed - CPU Virtual Mode active",
        });
      }
    }
  }

  startFramePump() {
    const pump = async () => {
      if (
        !this.webglDisabled &&
        this.faceMesh &&
        this.videoElement &&
        this.videoElement.readyState >= 2 &&
        this.videoElement.videoWidth > 0 &&
        this.videoElement.videoHeight > 0 &&
        !this.isProcessingFrame
      ) {
        this.isProcessingFrame = true;
        try {
          await this.faceMesh.send({ image: this.videoElement });
          this.consecutiveFailures = 0;
        } catch (err) {
          const errMsg = (err && err.message) ? err.message : String(err);
          this.consecutiveFailures++;

          // Catch WebGL canvas context failures and disable gracefully
          if (
            errMsg.toLowerCase().includes("webgl") ||
            errMsg.toLowerCase().includes("context") ||
            this.consecutiveFailures >= 3
          ) {
            console.warn(`[FaceTracker] WebGL failure detected ("${errMsg}"). Switching gracefully to CPU Virtual Mode.`);
            this.webglDisabled = true;
            if (this.onStatusChange) {
              this.onStatusChange({
                webgl: false,
                mode: "cpu_virtual",
                message: "WebGL context lost - CPU Virtual Mode active",
              });
            }
          }
        } finally {
          this.isProcessingFrame = false;
        }
      }
      requestAnimationFrame(pump);
    };
    requestAnimationFrame(pump);
  }

  initKeyboardListeners() {
    window.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.code === "Space" || e.code === "KeyJ") {
        this.triggerExpression("jawOpen", 1.0, 320);
      }
      if (e.code === "KeyS") {
        this.triggerExpression("smile", 1.0, 320);
      }
      if (e.code === "KeyB") {
        this.triggerExpression("browRaise", 1.0, 320);
      }
    });
  }

  triggerExpression(exprName, intensity = 1.0, durationMs = 300) {
    if (this.triggerTimeouts[exprName]) {
      clearTimeout(this.triggerTimeouts[exprName]);
    }

    this.expressions[exprName] = intensity;
    if (this.onResultsCallback) {
      this.onResultsCallback(this.expressions, this.lastLandmarks);
    }

    this.triggerTimeouts[exprName] = setTimeout(() => {
      this.expressions[exprName] = 0.0;
      if (this.onResultsCallback) {
        this.onResultsCallback(this.expressions, this.lastLandmarks);
      }
    }, durationMs);
  }

  setAutoGroove(enabled) {
    this.autoGroove = enabled;
    if (this.autoGrooveInterval) {
      clearInterval(this.autoGrooveInterval);
      this.autoGrooveInterval = null;
    }
    if (enabled) {
      const exprs = ["jawOpen", "smile", "browRaise"];
      let idx = 0;
      this.autoGrooveInterval = setInterval(() => {
        if (!this.autoGroove) return;
        const expr = exprs[idx % exprs.length];
        idx++;
        this.triggerExpression(expr, 1.0, 260);
      }, 550);
    }
  }

  processResults(results) {
    if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
      this.lastLandmarks = null;
      for (const k of ["jawOpen", "smile", "browRaise"]) {
        if (!this.triggerTimeouts[k]) {
          this.expressions[k] *= 0.7;
        }
      }
      if (this.onResultsCallback) this.onResultsCallback(this.expressions, null);
      return;
    }

    const lm = results.multiFaceLandmarks[0];
    this.lastLandmarks = lm;

    // Helper: 2D Euclidean Distance
    const dist = (i, j) => {
      const dx = lm[i].x - lm[j].x;
      const dy = lm[i].y - lm[j].y;
      return Math.sqrt(dx * dx + dy * dy);
    };

    const eyeSpan = dist(33, 263) || 0.2;
    const faceHeight = dist(10, 152) || 0.4;

    const rawJaw = dist(13, 14) / faceHeight;
    const rawSmile = dist(61, 291) / eyeSpan;
    const leftBrow = dist(105, 159);
    const rightBrow = dist(334, 386);
    const rawBrow = ((leftBrow + rightBrow) / 2.0) / faceHeight;

    if (this.isCalibrating) {
      this.calibrationFrames.push({ jaw: rawJaw, smile: rawSmile, brow: rawBrow });
      if (this.calibrationFrames.length >= 30) {
        this.finishCalibration();
      }
    }

    const normJaw = Math.max(0, Math.min(1.0, (rawJaw - this.baseline.jawOpen) / 0.18));
    const normSmile = Math.max(0, Math.min(1.0, (rawSmile - this.baseline.smile) / 0.16));
    const normBrow = Math.max(0, Math.min(1.0, (rawBrow - this.baseline.browRaise) / 0.08));

    if (!this.triggerTimeouts["jawOpen"]) {
      this.expressions.jawOpen = this.expressions.jawOpen * 0.4 + normJaw * 0.6;
    }
    if (!this.triggerTimeouts["smile"]) {
      this.expressions.smile = this.expressions.smile * 0.4 + normSmile * 0.6;
    }
    if (!this.triggerTimeouts["browRaise"]) {
      this.expressions.browRaise = this.expressions.browRaise * 0.4 + normBrow * 0.6;
    }

    if (this.onResultsCallback) {
      this.onResultsCallback(this.expressions, lm);
    }
  }

  calibrate() {
    this.isCalibrating = true;
    this.calibrationFrames = [];
    console.log("[FaceTracker] Calibrating resting baseline...");
  }

  finishCalibration() {
    this.isCalibrating = false;
    const count = this.calibrationFrames.length;
    if (count > 0) {
      const avgJaw = this.calibrationFrames.reduce((acc, f) => acc + f.jaw, 0) / count;
      const avgSmile = this.calibrationFrames.reduce((acc, f) => acc + f.smile, 0) / count;
      const avgBrow = this.calibrationFrames.reduce((acc, f) => acc + f.brow, 0) / count;

      this.baseline.jawOpen = avgJaw;
      this.baseline.smile = avgSmile;
      this.baseline.browRaise = avgBrow;
      console.log("[FaceTracker] Calibrated baseline:", this.baseline);
    }
  }
}

window.FaceTracker = FaceTracker;
