/**
 * camera.js - Dual-Mode Webcam & Cyber Avatar Stream Manager for FaceBeat-Studio.
 * Automatically uses physical webcam when available, and seamlessly falls back to
 * an interactive animated Cyber Avatar stream when no camera hardware is present.
 */
class CameraManager {
  constructor(videoElementId) {
    this.videoElement = document.getElementById(videoElementId);
    this.stream = null;
    this.isStreaming = false;
    this.isVirtual = false;

    // Virtual Avatar generator properties
    this.virtualCanvas = null;
    this.virtualCtx = null;
    this.virtualAnimId = null;
    this.avatarState = {
      jawOpen: 0.0,
      smile: 0.0,
      browRaise: 0.0,
      blink: 0.0,
      lastBlink: performance.now(),
      pulse: 0.0,
    };
  }

  async requestPhysicalCamera(statusCallback = null) {
    if (window.isSecureContext === false) {
      const err = new Error("INSECURE_ORIGIN: Chrome & Safari block camera access on remote HTTP. Access via http://localhost:8000 or HTTPS.");
      err.code = "INSECURE_ORIGIN";
      throw err;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const err = new Error("MEDIA_DEVICES_UNAVAILABLE: Browser mediaDevices API is not available on this origin or browser.");
      err.code = "MEDIA_DEVICES_UNAVAILABLE";
      throw err;
    }

    if (statusCallback) statusCallback("waiting_permission", "Waiting for browser/macOS camera approval...");

    let stream = null;
    let lastError = null;

    // Attempt 1: Standard 720p HD
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
    } catch (e1) {
      lastError = e1;
      // Attempt 2: Minimalist constraint fallback for desktop and USB webcams
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      } catch (e2) {
        lastError = e2;
      }
    }

    if (!stream) {
      const msg = lastError ? (lastError.message || lastError.name) : "Webcam access failed";
      const err = new Error(msg);
      err.name = lastError ? lastError.name : "CameraError";
      throw err;
    }

    // Stop virtual avatar loop if active
    if (this.virtualAnimId) {
      cancelAnimationFrame(this.virtualAnimId);
      this.virtualAnimId = null;
    }
    this.stopPhysicalStream();

    this.stream = stream;
    this.videoElement.srcObject = stream;
    this.isVirtual = false;
    this.isStreaming = true;

    await new Promise((resolve) => {
      this.videoElement.onloadedmetadata = () => {
        this.videoElement.play().catch(() => {});
        resolve();
      };
      setTimeout(resolve, 800);
    });

    if (statusCallback) statusCallback("connected", "Physical PC camera stream active.");
    console.log("[CameraManager] Physical PC camera stream active.");
    return { mode: "webcam", element: this.videoElement };
  }

  async initialize() {
    // Attempt physical camera with a fast timeout so page load never freezes waiting for permissions
    try {
      const physicalPromise = this.requestPhysicalCamera();
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("PROBE_TIMEOUT")), 1200)
      );
      return await Promise.race([physicalPromise, timeoutPromise]);
    } catch (err) {
      if (err.message === "PROBE_TIMEOUT") {
        console.log("[CameraManager] Camera approval pending or not immediate. Starting Virtual Avatar so UI is ready.");
      } else {
        console.warn("[CameraManager] Physical webcam could not be accessed immediately:", err.message);
      }
      return this.startVirtualAvatar();
    }
  }

  startVirtualAvatar() {
    this.isVirtual = true;
    this.stopPhysicalStream();

    if (!this.virtualCanvas) {
      this.virtualCanvas = document.createElement("canvas");
      this.virtualCanvas.width = 1280;
      this.virtualCanvas.height = 720;
      this.virtualCtx = this.virtualCanvas.getContext("2d");
    }

    // Capture 30 FPS stream from offscreen avatar canvas
    try {
      this.stream = this.virtualCanvas.captureStream(30);
      this.videoElement.srcObject = this.stream;
      this.videoElement.play().catch(() => {});
    } catch (e) {
      console.warn("[CameraManager] captureStream failed:", e);
    }

    this.isStreaming = true;
    this.runVirtualAvatarLoop();

    console.log("[CameraManager] Virtual Cyber Avatar active.");
    return Promise.resolve({ mode: "virtual", element: this.videoElement });
  }

  setAvatarExpressions(expr) {
    if (!expr) return;
    this.avatarState.jawOpen = expr.jawOpen || 0;
    this.avatarState.smile = expr.smile || 0;
    this.avatarState.browRaise = expr.browRaise || 0;
  }

  runVirtualAvatarLoop() {
    const ctx = this.virtualCtx;
    const w = this.virtualCanvas.width;
    const h = this.virtualCanvas.height;

    const render = (time) => {
      if (!this.isVirtual) return;

      // Handle natural blinking
      if (time - this.avatarState.lastBlink > 3000 + Math.random() * 2000) {
        this.avatarState.blink = 1.0;
        this.avatarState.lastBlink = time;
      }
      if (this.avatarState.blink > 0) {
        this.avatarState.blink -= 0.15;
        if (this.avatarState.blink < 0) this.avatarState.blink = 0;
      }

      this.avatarState.pulse = Math.sin(time * 0.003) * 0.5 + 0.5;

      // Clear with dark cyber gradient
      const bgGrad = ctx.createRadialGradient(w / 2, h / 2, 80, w / 2, h / 2, 600);
      bgGrad.addColorStop(0, "#19113b");
      bgGrad.addColorStop(1, "#070414");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, w, h);

      // Cyber Grid Lines (Background)
      ctx.strokeStyle = "rgba(0, 243, 255, 0.06)";
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 60) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += 60) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      const cx = w / 2;
      const cy = h / 2 + 30;

      // Outer Holographic Halo
      ctx.save();
      ctx.strokeStyle = `rgba(0, 243, 255, ${0.15 + this.avatarState.pulse * 0.2})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(cx, cy - 20, 220 + this.avatarState.pulse * 8, 0, Math.PI * 2);
      ctx.stroke();

      // Cyber Head Silhouette
      ctx.fillStyle = "rgba(18, 12, 45, 0.9)";
      ctx.strokeStyle = "rgba(139, 92, 246, 0.7)";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.ellipse(cx, cy - 20, 160, 210, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Eyebrows (react to browRaise)
      const browOffset = -this.avatarState.browRaise * 35;
      ctx.strokeStyle = "#ff007f";
      ctx.lineWidth = 6;
      ctx.beginPath();
      // Left Eyebrow
      ctx.moveTo(cx - 90, cy - 110 + browOffset);
      ctx.lineTo(cx - 30, cy - 118 + browOffset);
      // Right Eyebrow
      ctx.moveTo(cx + 30, cy - 118 + browOffset);
      ctx.lineTo(cx + 90, cy - 110 + browOffset);
      ctx.stroke();

      // Eyes (react to blink)
      const eyeOpen = Math.max(2, 22 * (1.0 - this.avatarState.blink));
      ctx.fillStyle = "#00f3ff";
      ctx.shadowColor = "#00f3ff";
      ctx.shadowBlur = 15;

      // Left Eye
      ctx.beginPath();
      ctx.ellipse(cx - 60, cy - 70, 24, eyeOpen, 0, 0, Math.PI * 2);
      ctx.fill();

      // Right Eye
      ctx.beginPath();
      ctx.ellipse(cx + 60, cy - 70, 24, eyeOpen, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Nose Bridge Accent
      ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy - 50);
      ctx.lineTo(cx, cy + 10);
      ctx.lineTo(cx + 10, cy + 18);
      ctx.stroke();

      // Mouth (reacts to jawOpen and smile)
      const mouthY = cy + 70 + this.avatarState.jawOpen * 20;
      const mouthWidth = 40 + this.avatarState.smile * 40;
      const mouthHeight = Math.max(4, 8 + this.avatarState.jawOpen * 50);

      ctx.fillStyle = this.avatarState.smile > 0.5 ? "#ffd700" : "#ff007f";
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;

      ctx.beginPath();
      if (this.avatarState.jawOpen > 0.25) {
        // Open mouth ellipse
        ctx.ellipse(cx, mouthY, mouthWidth, mouthHeight, 0, 0, Math.PI * 2);
        ctx.fill();
      } else {
        // Closed / Smiling mouth arc
        const curve = this.avatarState.smile * 25;
        ctx.beginPath();
        ctx.moveTo(cx - mouthWidth, mouthY);
        ctx.quadraticCurveTo(cx, mouthY + curve + 10, cx + mouthWidth, mouthY);
        ctx.stroke();
      }

      // Watermark Text
      ctx.font = "bold 16px Inter, sans-serif";
      ctx.fillStyle = "rgba(0, 243, 255, 0.6)";
      ctx.textAlign = "center";
      ctx.fillText("🤖 VIRTUAL AVATAR FEED (INTERACTIVE CAMERA REPLACEMENT)", cx, h - 30);
      ctx.restore();

      this.virtualAnimId = requestAnimationFrame(render);
    };

    this.virtualAnimId = requestAnimationFrame(render);
  }

  stopPhysicalStream() {
    if (this.stream) {
      try {
        this.stream.getTracks().forEach((track) => track.stop());
      } catch (e) {}
    }
  }

  stop() {
    this.stopPhysicalStream();
    if (this.virtualAnimId) {
      cancelAnimationFrame(this.virtualAnimId);
      this.virtualAnimId = null;
    }
    this.isStreaming = false;
  }
}

window.CameraManager = CameraManager;
