/**
 * recorder.js - In-browser session recording and upload to SocialClipperAgent.
 */
class SessionRecorder {
  constructor(canvasElement, videoElement) {
    this.canvas = canvasElement;
    this.video = videoElement;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isRecording = false;
  }

  startRecording() {
    this.recordedChunks = [];

    // Capture visual canvas stream at 30 FPS
    let stream;
    try {
      stream = this.canvas.captureStream(30);
    } catch (e) {
      console.warn("[SessionRecorder] Canvas captureStream failed:", e);
      return;
    }

    const mimeTypes = [
      "video/webm;codecs=vp9,opus",
      "video/webm;codecs=vp8,opus",
      "video/webm",
      "video/mp4",
    ];

    let selectedMime = mimeTypes.find((m) => MediaRecorder.isTypeSupported(m)) || "";

    try {
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedMime || undefined,
        videoBitsPerSecond: 2500000, // 2.5 Mbps
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(1000); // 1-second timeslices
      this.isRecording = true;
      console.log("[SessionRecorder] Started game session recording.");
    } catch (err) {
      console.error("[SessionRecorder] MediaRecorder initialization failed:", err);
    }
  }

  start() {
    return this.startRecording();
  }

  async stop() {
    if (!this.isRecording || !this.mediaRecorder) return null;
    return new Promise((resolve) => {
      this.mediaRecorder.onstop = () => {
        this.isRecording = false;
        const blob = new Blob(this.recordedChunks, { type: "video/webm" });
        resolve(blob);
      };
      this.mediaRecorder.stop();
    });
  }

  async uploadRecording(blob) {
    if (!blob) throw new Error("No video blob provided for upload.");
    const formData = new FormData();
    formData.append("video", blob, "session_recording.webm");

    const res = await fetch("/api/clipper/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Video upload failed.");
    return await res.json();
  }

  async stopAndUpload() {
    const blob = await this.stop();
    if (!blob) return null;
    const data = await this.uploadRecording(blob);
    return data.filename;
  }
}

window.SessionRecorder = SessionRecorder;
