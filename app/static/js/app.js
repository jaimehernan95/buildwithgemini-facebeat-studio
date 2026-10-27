/**
 * app.js - Main Application Orchestrator for FaceBeat-Studio.
 * Coordinates Camera, Face Tracking, Game Engine, Recorder, and Backend APIs.
 */
class FaceBeatApp {
  constructor() {
    this.camera = new CameraManager("webcam");
    this.audio = document.getElementById("gameAudio");
    this.gameEngine = null;
    this.faceTracker = null;
    this.recorder = null;

    this.currentTrack = "lofi_piano_chill.wav";
    this.currentDifficulty = "normal";
    this.currentBeatmap = null;
    this.lastUploadedVideo = null;
    this.currentScore = 0;
    this.maxCombo = 0;
    this.isAutoGrooveOn = false;

    this.initDOMElements();
  }

  initDOMElements() {
    this.btnStart = document.getElementById("btnStartGame");
    this.btnLoopTrack = document.getElementById("btnLoopTrack");
    this.btnCalibrate = document.getElementById("btnCalibrate");
    this.btnExport = document.getElementById("btnExportClip");
    this.btnSwitchCamera = document.getElementById("btnSwitchCamera");
    this.btnCamGuide = document.getElementById("btnCamGuide");
    this.cameraStatusPill = document.getElementById("cameraStatusPill");
    this.webglStatusPill = document.getElementById("webglStatusPill");
    this.btnAutoGroove = document.getElementById("btnAutoGroove");
    this.btnLeaderboard = document.getElementById("btnLeaderboard");
    this.leaderboardModal = document.getElementById("leaderboardModal");
    this.leaderboardBody = document.getElementById("leaderboardBody");
    this.camGuideModal = document.getElementById("camGuideModal");
    this.stageClearModal = document.getElementById("stageClearModal");
    this.btnWatchDemo = document.getElementById("btnWatchDemo");
    this.demoVideoModal = document.getElementById("demoVideoModal");
    this.demoVideoPlayer = document.getElementById("demoVideoPlayer");

    this.btnBrowseMusic = document.getElementById("btnBrowseMusic");
    this.musicBrowserModal = document.getElementById("musicBrowserModal");
    this.spotifyConnectModal = document.getElementById("spotifyConnectModal");
    this.tabJamendo = document.getElementById("tabJamendo");
    this.tabSpotify = document.getElementById("tabSpotify");
    this.musicSearchInput = document.getElementById("musicSearchInput");
    this.musicResultsContainer = document.getElementById("musicResultsContainer");
    this.musicPreviewAudio = document.getElementById("musicPreviewAudio");
    this.musicSourceNotice = document.getElementById("musicSourceNotice");
    this.activeMusicTab = "jamendo";
    this.currentlyPlayingPreviewId = null;

    this.songProgressBar = document.getElementById("songProgressBar");
    this.songTimeCurrent = document.getElementById("songTimeCurrent");
    this.songTimeTotal = document.getElementById("songTimeTotal");
    this.songLoopIndicator = document.getElementById("songLoopIndicator");
    this.statTotalGames = document.getElementById("statTotalGames");
    this.statHighScore = document.getElementById("statHighScore");
    this.statMaxCombo = document.getElementById("statMaxCombo");
    this.playerNameInput = document.getElementById("playerNameInput");

    this.trackSelect = document.getElementById("trackSelect");
    this.difficultySelect = document.getElementById("difficultySelect");
    this.scoreDisplay = document.getElementById("scoreDisplay");
    this.comboDisplay = document.getElementById("comboDisplay");

    this.barJaw = document.getElementById("barJaw");
    this.barSmile = document.getElementById("barSmile");
    this.barBrow = document.getElementById("barBrow");
    this.valJaw = document.getElementById("valJaw");
    this.valSmile = document.getElementById("valSmile");
    this.valBrow = document.getElementById("valBrow");

    this.agentConsole = document.getElementById("agentConsole");
    this.agentPromptInput = document.getElementById("agentPromptInput");
    this.btnSendAgent = document.getElementById("btnSendAgent");
    this.clipModal = document.getElementById("clipModal");
    this.clipVideoPlayer = document.getElementById("clipVideoPlayer");
    this.btnDownloadClip = document.getElementById("btnDownloadClip");
    this.calibrationBanner = document.getElementById("calibrationBanner");

    // Quick trigger buttons
    this.btnTriggerJaw = document.getElementById("btnTriggerJaw");
    this.btnTriggerSmile = document.getElementById("btnTriggerSmile");
    this.btnTriggerBrow = document.getElementById("btnTriggerBrow");

    // Event Listeners
    this.btnStart.addEventListener("click", () => this.toggleGame());
    if (this.btnLoopTrack) {
      this.btnLoopTrack.addEventListener("click", () => this.toggleLoopTrack());
    }
    this.btnCalibrate.addEventListener("click", () => this.calibrateFace());
    this.btnExport.addEventListener("click", () => this.exportClip());

    if (this.btnLeaderboard) {
      this.btnLeaderboard.addEventListener("click", () => this.openLeaderboard());
    }

    if (this.btnWatchDemo) {
      this.btnWatchDemo.addEventListener("click", () => this.openDemoVideoModal());
    }

    if (this.btnBrowseMusic) {
      this.btnBrowseMusic.addEventListener("click", () => this.openMusicModal());
    }

    if (this.musicSearchInput) {
      this.musicSearchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this.executeMusicSearch();
      });
    }

    const badgeSpotify = document.getElementById("badgeSpotify");
    if (badgeSpotify) {
      badgeSpotify.addEventListener("click", () => this.connectSpotify());
    }

    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        this.closeAllModals();
      }
    });

    if (this.btnAutoGroove) {
      this.btnAutoGroove.addEventListener("click", () => this.toggleAutoGroove());
    }

    if (this.btnSwitchCamera) {
      this.btnSwitchCamera.addEventListener("click", () => this.toggleCameraMode());
    }

    if (this.btnCamGuide) {
      this.btnCamGuide.addEventListener("click", () => this.openCamGuideModal());
    }

    if (this.btnTriggerJaw) {
      this.btnTriggerJaw.addEventListener("click", () => {
        if (this.faceTracker) this.faceTracker.triggerExpression("jawOpen", 1.0, 350);
      });
    }
    if (this.btnTriggerSmile) {
      this.btnTriggerSmile.addEventListener("click", () => {
        if (this.faceTracker) this.faceTracker.triggerExpression("smile", 1.0, 350);
      });
    }
    if (this.btnTriggerBrow) {
      this.btnTriggerBrow.addEventListener("click", () => {
        if (this.faceTracker) this.faceTracker.triggerExpression("browRaise", 1.0, 350);
      });
    }

    this.trackSelect.addEventListener("change", (e) => this.onTrackChanged(e.target.value));
    this.difficultySelect.addEventListener("change", (e) => this.onDifficultyChanged(e.target.value));
    this.btnSendAgent.addEventListener("click", () => this.sendAgentPrompt());
    this.agentPromptInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.sendAgentPrompt();
    });
  }

  updateCameraStatus() {
    if (this.cameraStatusPill) {
      if (this.camera.isVirtual) {
        this.cameraStatusPill.className = "camera-status-pill virtual";
        this.cameraStatusPill.innerHTML = "🤖 Virtual Avatar Mode";
      } else {
        this.cameraStatusPill.className = "camera-status-pill";
        this.cameraStatusPill.innerHTML = "📹 Physical Webcam Active";
      }
    }
    if (this.btnSwitchCamera) {
      if (this.camera.isVirtual) {
        this.btnSwitchCamera.textContent = "📹 Turn On PC Camera";
        this.btnSwitchCamera.title = "Request browser webcam permissions to turn on PC camera";
      } else {
        this.btnSwitchCamera.textContent = "🤖 Switch to Virtual Avatar";
        this.btnSwitchCamera.title = "Switch back to animated Virtual Cyber Avatar";
      }
    }
  }

  onTrackerStatusChange(status) {
    if (!this.webglStatusPill) return;
    if (status.webgl) {
      this.webglStatusPill.className = "camera-status-pill";
      this.webglStatusPill.innerHTML = "⚡ WebGL: Active";
    } else {
      this.webglStatusPill.className = "camera-status-pill virtual";
      this.webglStatusPill.innerHTML = "⚡ WebGL: CPU Fallback";
      this.logAgent("FaceTracker", status.message || "WebGL context unavailable. CPU Virtual Mode active.");
    }
  }

  toggleAutoGroove() {
    this.isAutoGrooveOn = !this.isAutoGrooveOn;
    if (this.faceTracker) {
      this.faceTracker.setAutoGroove(this.isAutoGrooveOn);
    }
    if (this.btnAutoGroove) {
      if (this.isAutoGrooveOn) {
        this.btnAutoGroove.textContent = "🤖 Auto-Groove: ON";
        this.btnAutoGroove.style.background = "rgba(139, 92, 246, 0.4)";
        this.logAgent("SYSTEM", "Auto-Groove test mode enabled. Simulated rhythm is triggering facial expressions.");
      } else {
        this.btnAutoGroove.textContent = "🤖 Auto-Groove: OFF";
        this.btnAutoGroove.style.background = "rgba(139, 92, 246, 0.2)";
        this.logAgent("SYSTEM", "Auto-Groove test mode disabled.");
      }
    }
  }

  async toggleCameraMode() {
    if (this.camera.isVirtual) {
      this.logAgent("Camera", "Requesting browser permission for physical PC webcam...");
      try {
        await this.camera.requestPhysicalCamera((state, msg) => {
          this.logAgent("Camera", msg);
        });
        this.logAgent("Camera", "Physical webcam connected! Live camera feed active.");
      } catch (err) {
        let hint = "";
        if (window.isSecureContext === false) {
          hint = " [Tip: Origin is insecure. To use MacBook camera, access via http://localhost:8000 via SSH tunnel]";
        } else if (err.name === "NotAllowedError" || (err.message && err.message.includes("Permission"))) {
          hint = " [Tip: Click '❓ Mac/Cam Help' above to see macOS System Settings & URL lock instructions]";
        }
        this.logAgent("Camera", `Webcam access denied/unavailable: ${err.message}.${hint}`);
        this.openCamGuideModal();
      }
    } else {
      this.camera.startVirtualAvatar();
      this.logAgent("Camera", "Switched to animated Virtual Cyber Avatar.");
    }
    this.updateCameraStatus();
  }

  async initialize() {
    this.logAgent("SYSTEM", "Initializing FaceBeat-Studio...");

    if (window.isSecureContext === false && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      this.logAgent("SYSTEM", "⚠️ Notice: Remote HTTP origin detected. Modern browsers restrict webcams on remote HTTP. Virtual Cyber Avatar & Auto-Groove modes are active!");
    }

    // 1. Initialize Camera (with automatic Virtual Avatar fallback)
    try {
      const camResult = await this.camera.initialize();
      this.updateCameraStatus();
      if (this.camera.isVirtual) {
        this.logAgent("Camera", "Virtual Cyber Avatar active. Click 'Turn On PC Camera' anytime to switch to your webcam!");
      } else {
        this.logAgent("Camera", "Physical PC webcam active (1280x720). Mirror feed ready.");
      }
    } catch (err) {
      console.warn("[FaceBeatApp] Camera setup error, defaulting to Virtual Avatar:", err);
      this.camera.startVirtualAvatar();
      this.updateCameraStatus();
    }

    // 2. Initialize Game Engine
    try {
      this.gameEngine = new GameEngine(
        "gameCanvas",
        "gameAudio",
        (stats) => this.onGameStats(stats),
        (finalStats) => this.onGameComplete(finalStats)
      );
      console.log("[FaceBeatApp] Game Engine initialized with idle highway loop.");
    } catch (e) {
      console.error("[FaceBeatApp] Game engine init error:", e);
    }

    // 3. Initialize Face Tracker
    try {
      this.faceTracker = new FaceTracker(
        this.camera.videoElement,
        (expr, lm) => this.onFaceData(expr, lm),
        (status) => this.onTrackerStatusChange(status)
      );
      await this.faceTracker.initialize();
      this.logAgent("FaceTracker", "Face expression classifier running.");
    } catch (e) {
      console.warn("[FaceBeatApp] Face tracker init error:", e);
    }

    // 4. Initialize Session Recorder
    try {
      const canvas = document.getElementById("gameCanvas");
      this.recorder = new SessionRecorder(canvas, this.camera.videoElement);
    } catch (e) {
      console.warn("[FaceBeatApp] Recorder init error:", e);
    }

    // 5. Load Initial Track & Beatmap
    await this.loadTrack(this.currentTrack);
  }

  async loadTrack(filename) {
    this.currentTrack = filename;

    // Check if filename is an online stream or full URL
    const isOnline = filename.startsWith("http://") || filename.startsWith("https://");
    const audioUrl = isOnline ? filename : (filename.startsWith("/static/") ? filename : `/static/audio/${filename}`);

    if (this.audio) {
      this.audio.src = audioUrl;
      this.audio.currentTime = 0;
      this.audio.load();
    }
    if (this.gameEngine && this.gameEngine.audio) {
      this.gameEngine.audio.src = audioUrl;
      this.gameEngine.audio.currentTime = 0;
      this.gameEngine.audio.load();
    }

    if (isOnline) {
      this.logAgent("RhythmAnalyzer", `Stream ready: ${this.currentTrackTitle || "Online Track"}`);
      this.btnStart.disabled = false;
      return;
    }

    this.logAgent("RhythmAnalyzer", `Requesting beat analysis for '${filename}' (${this.currentDifficulty})...`);

    try {
      const cleanFilename = filename.replace(/^\/static\/audio\//, "");
      // Safety Check
      const safetyRes = await fetch("/api/tracks/safety-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_title: cleanFilename }),
      });
      const safety = await safetyRes.json();
      this.logAgent("AudioSafety", `Copyright status: ${safety.status} (Risk: ${safety.risk_score})`);

      // Beatmap Analysis
      const res = await fetch("/api/tracks/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: cleanFilename, difficulty: this.currentDifficulty }),
      });
      const beatmap = await res.json();
      this.currentBeatmap = beatmap;
      if (this.gameEngine) {
        this.gameEngine.loadBeatmap(beatmap);
      }

      this.logAgent("RhythmAnalyzer", `Beatmap generated: ${beatmap.bpm} BPM, ${beatmap.total_targets} expression targets.`);
      this.btnStart.disabled = false;
      this.updateNowPlayingBadge(cleanFilename.replace(/_/g, " ").replace(".wav", ""));
    } catch (err) {
      this.logAgent("ERROR", `Failed to analyze track: ${err.message}`);
    }
  }

  onTrackChanged(val) {
    if (this.gameEngine && this.gameEngine.isPlaying) this.toggleGame();
    this.loadTrack(val);
  }

  onDifficultyChanged(val) {
    this.currentDifficulty = val;
    if (this.currentTrack) this.loadTrack(this.currentTrack);
  }

  onFaceData(expressions, landmarks) {
    // Update live expression gauges
    const jawPct = Math.round(expressions.jawOpen * 100);
    const smilePct = Math.round(expressions.smile * 100);
    const browPct = Math.round(expressions.browRaise * 100);

    if (this.barJaw) this.barJaw.style.width = `${jawPct}%`;
    if (this.barSmile) this.barSmile.style.width = `${smilePct}%`;
    if (this.barBrow) this.barBrow.style.width = `${browPct}%`;

    if (this.valJaw) this.valJaw.textContent = `${jawPct}%`;
    if (this.valSmile) this.valSmile.textContent = `${smilePct}%`;
    if (this.valBrow) this.valBrow.textContent = `${browPct}%`;

    // Forward to cyber avatar if in virtual mode
    if (this.camera && this.camera.isVirtual) {
      this.camera.setAvatarExpressions(expressions);
    }

    // Forward to game engine
    if (this.gameEngine) {
      this.gameEngine.updateExpressions(expressions, landmarks);
    }
  }

  onGameStats(stats) {
    this.currentScore = stats.score;
    this.maxCombo = stats.maxCombo;
    if (this.scoreDisplay) this.scoreDisplay.textContent = stats.score.toLocaleString();
    if (this.comboDisplay) this.comboDisplay.textContent = `${stats.combo}x`;

    if (this.songProgressBar && stats.progress !== undefined) {
      this.songProgressBar.style.width = `${stats.progress.toFixed(1)}%`;
    }
    if (this.songTimeCurrent && stats.currentTime !== undefined) {
      this.songTimeCurrent.textContent = this.formatTime(stats.currentTime);
    }
    if (this.songTimeTotal && stats.duration !== undefined) {
      this.songTimeTotal.textContent = this.formatTime(stats.duration);
    }
    if (this.songLoopIndicator && stats.isLooping !== undefined) {
      this.songLoopIndicator.textContent = stats.isLooping ? "🔁 Loop: ON" : "⏹ Single Play";
      this.songLoopIndicator.style.color = stats.isLooping ? "#00f3ff" : "#888";
    }
  }

  formatTime(seconds) {
    const s = Math.floor(seconds || 0);
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}:${rem < 10 ? "0" : ""}${rem}`;
  }

  toggleLoopTrack() {
    if (!this.gameEngine) return;
    const nextState = !this.gameEngine.isLooping;
    this.gameEngine.setLooping(nextState);
    if (this.btnLoopTrack) {
      this.btnLoopTrack.textContent = nextState ? "🔁 Loop: ON" : "🔁 Loop: OFF";
      this.btnLoopTrack.style.color = nextState ? "#00f3ff" : "#888";
      this.btnLoopTrack.style.borderColor = nextState ? "#00f3ff" : "#444";
    }
    this.logAgent("SYSTEM", `Looping mode set to: ${nextState ? "ON (Infinite Groove)" : "OFF (Single Run)"}`);
  }

  async toggleGame() {
    if (!this.gameEngine) return;

    if (this.gameEngine.isPlaying) {
      // Stop Game
      const finalStats = this.gameEngine.getFinalStats();
      this.gameEngine.stop();
      this.btnStart.textContent = "▶ Start Game";
      this.btnStart.classList.remove("btn-cyan");

      // Auto-save session to SQLite
      await this.onGameComplete(finalStats);

      // Stop recorder
      if (this.recorder && this.recorder.isRecording) {
        this.logAgent("SocialClipper", "Finishing session capture...");
        try {
          const blob = await this.recorder.stop();
          this.logAgent("SocialClipper", `Recorded ${(blob.size / 1024).toFixed(1)} KB video. Uploading...`);

          const uploadData = await this.recorder.uploadRecording(blob);
          this.lastUploadedVideo = uploadData.filename;
          this.btnExport.disabled = false;
          this.logAgent("SocialClipper", "Video clip ready for 9:16 vertical render.");
        } catch (err) {
          this.logAgent("SocialClipper", `Capture failed: ${err.message}`);
        }
      }
    } else {
      // Start Game
      // 1. Forcefully stop and reset AI Demo video if playing or open
      this.closeDemoVideoModal();
      if (this.demoVideoPlayer) {
        this.demoVideoPlayer.pause();
        this.demoVideoPlayer.currentTime = 0;
      }
      // 2. Stop any music preview audio and close music browsers
      if (this.musicPreviewAudio) {
        this.musicPreviewAudio.pause();
        this.musicPreviewAudio.currentTime = 0;
      }
      this.closeMusicModal();
      this.closeSpotifyModal();

      this.gameEngine.start();
      this.btnStart.textContent = "⏹ Stop Game";
      this.btnStart.classList.add("btn-cyan");
      this.btnExport.disabled = true;

      // Start recorder
      if (this.recorder) {
        try {
          this.recorder.start();
          this.logAgent("SocialClipper", "Recording live session stream...");
        } catch (err) {
          console.warn("[FaceBeatApp] Recorder start warning:", err);
        }
      }

      this.logAgent("RhythmAnalyzer", "Beat stream active! Match facial expressions to incoming notes!");
    }
  }

  async onGameComplete(finalStats) {
    this.btnStart.textContent = "▶ Start Game";
    this.btnStart.classList.remove("btn-cyan");

    if (finalStats && finalStats.score > 0) {
      this.logAgent(
        "GAME",
        `Game Complete! Score: ${finalStats.score.toLocaleString()} | Max Combo: ${finalStats.maxCombo}x | Grade: ${finalStats.grade}`
      );
      await this.saveGameSessionToDatabase(finalStats);
      this.showStageClearModal(finalStats);
    }
  }

  showStageClearModal(stats) {
    if (!this.stageClearModal) return;
    const trackTitle = this.trackSelect ? this.trackSelect.options[this.trackSelect.selectedIndex]?.text : "FaceBeat Track";
    const trackEl = document.getElementById("clearTrackTitle");
    const scoreEl = document.getElementById("clearScore");
    const accEl = document.getElementById("clearAccuracy");
    const perfEl = document.getElementById("clearPerfect");
    const greatEl = document.getElementById("clearGreat");
    const goodEl = document.getElementById("clearGood");
    const missEl = document.getElementById("clearMiss");
    const badgeEl = document.getElementById("clearGradeBadge");

    if (trackEl) trackEl.textContent = trackTitle;
    if (scoreEl) scoreEl.textContent = (stats.score || 0).toLocaleString();
    if (accEl) accEl.textContent = `Accuracy: ${stats.accuracy || 100}%`;
    if (perfEl) perfEl.textContent = stats.perfectHits || 0;
    if (greatEl) greatEl.textContent = stats.greatHits || 0;
    if (goodEl) goodEl.textContent = stats.goodHits || 0;
    if (missEl) missEl.textContent = stats.misses || 0;

    if (badgeEl) {
      badgeEl.textContent = stats.grade || "A";
      const colors = {
        S: "linear-gradient(135deg, #ffd700, #ff8800)",
        A: "linear-gradient(135deg, #00f3ff, #0088ff)",
        B: "linear-gradient(135deg, #00ff88, #00aa44)",
        C: "linear-gradient(135deg, #ffaa00, #cc5500)",
      };
      badgeEl.style.background = colors[stats.grade] || colors.A;
    }

    this.stageClearModal.style.display = "flex";
  }

  closeStageClearModal() {
    if (this.stageClearModal) this.stageClearModal.style.display = "none";
  }

  playAgain() {
    this.closeStageClearModal();
    if (this.gameEngine && !this.gameEngine.isPlaying) {
      this.toggleGame();
    }
  }

  showLeaderboardModal() {
    this.closeStageClearModal();
    this.openLeaderboard();
  }

  openCamGuideModal() {
    if (!this.camGuideModal) return;
    this.camGuideModal.style.display = "flex";

    const originEl = document.getElementById("camDiagOrigin");
    const secureEl = document.getElementById("camDiagSecure");
    const mediaEl = document.getElementById("camDiagMedia");

    if (originEl) originEl.innerHTML = `<strong>Origin:</strong> ${window.location.origin}`;
    if (secureEl) {
      const isSec = window.isSecureContext;
      secureEl.innerHTML = `<strong>Secure Context:</strong> ${isSec ? "✅ Yes (Webcam API unlocked)" : "❌ NO (Remote HTTP blocks webcam in Chrome/Safari)"}`;
      secureEl.style.color = isSec ? "#00ff88" : "#ff3366";
    }
    if (mediaEl) {
      const hasMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
      mediaEl.innerHTML = `<strong>mediaDevices.getUserMedia:</strong> ${hasMedia ? "✅ Available" : "❌ Unavailable"}`;
      mediaEl.style.color = hasMedia ? "#00ff88" : "#ff3366";
    }
  }

  closeCamGuideModal() {
    if (this.camGuideModal) this.camGuideModal.style.display = "none";
  }

  openDemoVideoModal() {
    // If game is playing, stop it so audio doesn't overlap
    if (this.gameEngine && this.gameEngine.isPlaying) {
      this.toggleGame();
    }
    if (this.musicPreviewAudio) {
      this.musicPreviewAudio.pause();
      this.musicPreviewAudio.currentTime = 0;
    }
    if (!this.demoVideoModal) this.demoVideoModal = document.getElementById("demoVideoModal");
    if (!this.demoVideoPlayer) this.demoVideoPlayer = document.getElementById("demoVideoPlayer");
    if (!this.demoVideoModal) return;

    this.demoVideoModal.classList.add("active");
    this.demoVideoModal.style.display = "flex";
    if (this.demoVideoPlayer) {
      this.demoVideoPlayer.currentTime = 0;
      this.demoVideoPlayer.play().catch((err) => console.log("Demo autoplay preview prevented:", err));
    }
    this.logAgent("SYSTEM", "Playing AI Model Nova-7 gameplay demonstration.");
  }

  closeDemoVideoModal() {
    if (!this.demoVideoModal) this.demoVideoModal = document.getElementById("demoVideoModal");
    if (!this.demoVideoPlayer) this.demoVideoPlayer = document.getElementById("demoVideoPlayer");
    if (this.demoVideoPlayer) {
      this.demoVideoPlayer.pause();
      this.demoVideoPlayer.currentTime = 0;
    }
    if (this.demoVideoModal) {
      this.demoVideoModal.classList.remove("active");
      this.demoVideoModal.style.display = "none";
    }
  }

  openMusicModal() {
    this.closeDemoVideoModal();
    if (!this.musicBrowserModal) this.musicBrowserModal = document.getElementById("musicBrowserModal");
    if (!this.musicBrowserModal) return;

    this.musicBrowserModal.classList.add("active");
    this.musicBrowserModal.style.display = "flex";
    if (this.musicPreviewAudio) this.musicPreviewAudio.pause();
    this.executeMusicSearch();
  }

  closeMusicModal() {
    if (!this.musicBrowserModal) this.musicBrowserModal = document.getElementById("musicBrowserModal");
    if (!this.musicBrowserModal) return;

    this.musicBrowserModal.classList.remove("active");
    this.musicBrowserModal.style.display = "none";
    if (this.musicPreviewAudio) {
      this.musicPreviewAudio.pause();
      this.musicPreviewAudio.currentTime = 0;
      this.musicPreviewAudio.src = "";
    }
    this.currentlyPlayingPreviewId = null;
  }

  connectSpotify() {
    this.openSpotifyModal();
  }

  openSpotifyModal() {
    this.closeDemoVideoModal();
    if (!this.spotifyConnectModal) this.spotifyConnectModal = document.getElementById("spotifyConnectModal");
    if (!this.spotifyConnectModal) return;

    this.spotifyConnectModal.classList.add("active");
    this.spotifyConnectModal.style.display = "flex";
    this.logAgent("Spotify", "Opened Spotify Web API connection settings.");
  }

  closeSpotifyModal() {
    if (!this.spotifyConnectModal) this.spotifyConnectModal = document.getElementById("spotifyConnectModal");
    if (!this.spotifyConnectModal) return;

    this.spotifyConnectModal.classList.remove("active");
    this.spotifyConnectModal.style.display = "none";
  }

  closeAllModals() {
    this.closeDemoVideoModal();
    this.closeMusicModal();
    this.closeSpotifyModal();
    this.closeLeaderboard();
    this.closeCamGuideModal();
    this.closeStageClearModal();
    this.closeClipModal();
  }

  switchMusicTab(tab) {
    this.activeMusicTab = tab;
    if (this.tabJamendo) {
      if (tab === "jamendo") {
        this.tabJamendo.className = "btn";
        this.tabJamendo.style.background = "#a855f7";
        this.tabJamendo.style.color = "#fff";
      } else {
        this.tabJamendo.className = "btn btn-outline";
        this.tabJamendo.style.background = "transparent";
        this.tabJamendo.style.color = "#c084fc";
      }
    }
    if (this.tabSpotify) {
      if (tab === "spotify") {
        this.tabSpotify.className = "btn";
        this.tabSpotify.style.background = "#1db954";
        this.tabSpotify.style.color = "#fff";
      } else {
        this.tabSpotify.className = "btn btn-outline";
        this.tabSpotify.style.background = "transparent";
        this.tabSpotify.style.color = "#1db954";
      }
    }
    if (this.musicSourceNotice) {
      if (tab === "jamendo") {
        this.musicSourceNotice.innerHTML = "✅ <strong>Jamendo:</strong> 100% Creative Commons licensed, safe for social video clips.";
      } else {
        this.musicSourceNotice.innerHTML = "🎧 <strong>Spotify:</strong> Pop hits with official album artwork, artist metadata, and BPM.";
      }
    }
    this.executeMusicSearch();
  }

  async executeMusicSearch() {
    if (!this.musicSearchInput) this.musicSearchInput = document.getElementById("musicSearchInput");
    if (!this.musicResultsContainer) this.musicResultsContainer = document.getElementById("musicResultsContainer");
    const q = this.musicSearchInput ? this.musicSearchInput.value.trim() : "";
    if (!this.musicResultsContainer) return;
    this.musicResultsContainer.innerHTML = '<div style="text-align: center; color: #8b949e; padding: 30px;">⏳ Searching tracks...</div>';

    const endpoint = this.activeMusicTab === "jamendo"
      ? `/api/music/jamendo/search?q=${encodeURIComponent(q)}&limit=10`
      : `/api/music/spotify/search?q=${encodeURIComponent(q)}&limit=10`;

    try {
      const resp = await fetch(endpoint);
      const data = await resp.json();
      const tracks = data.tracks || [];
      this.renderMusicResults(tracks);
    } catch (err) {
      this.musicResultsContainer.innerHTML = `<div style="text-align: center; color: #ff3366; padding: 20px;">Failed to load tracks: ${err.message}</div>`;
    }
  }

  renderMusicResults(tracks) {
    if (!this.musicResultsContainer) return;
    if (!tracks || tracks.length === 0) {
      this.musicResultsContainer.innerHTML = '<div style="text-align: center; color: #8b949e; padding: 30px;">No tracks found. Try a different search!</div>';
      return;
    }

    this.musicResultsContainer.innerHTML = tracks.map((t) => {
      const sourceBadge = t.source === "jamendo"
        ? '<span style="background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid #a855f7; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;">Jamendo CC</span>'
        : '<span style="background: rgba(29,185,84,0.2); color: #1db954; border: 1px solid #1db954; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;">Spotify</span>';

      const bpmBadge = `<span style="background: rgba(0,243,255,0.15); color: #00f3ff; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px;">⚡ ${t.bpm || 120} BPM</span>`;
      const genreOrAlbum = t.genre || t.album || "Pop / Electronic";

      const escapedTrack = JSON.stringify(t).replace(/"/g, '&quot;');

      return `
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; background: rgba(255,255,255,0.03); border: 1px solid #30363d; border-radius: 8px; padding: 10px; transition: all 0.2s;">
          <img src="${t.cover_art}" alt="${t.title}" style="width: 52px; height: 52px; border-radius: 6px; object-fit: cover; flex-shrink: 0; border: 1px solid #484f58;" />
          <div style="flex: 1; min-width: 0;">
            <div style="font-weight: 600; font-size: 0.92rem; color: #f0f6fc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${t.title}
            </div>
            <div style="font-size: 0.8rem; color: #8b949e; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${t.artist} • <span style="color: #6e7681;">${genreOrAlbum}</span>
            </div>
            <div style="display: flex; gap: 6px; align-items: center;">
              ${sourceBadge}
              ${bpmBadge}
            </div>
          </div>
          <div style="display: flex; gap: 6px; align-items: center; flex-shrink: 0;">
            <button id="btnPrev_${t.id}" class="btn btn-outline" style="padding: 6px 10px; font-size: 0.8rem;" onclick="app.toggleMusicPreview('${t.id}', '${t.preview_url || t.stream_url}')">
              ▶ Preview
            </button>
            <button class="btn btn-cyan" style="padding: 6px 12px; font-size: 0.8rem;" onclick="app.selectOnlineTrack(${escapedTrack})">
              Select 🎮
            </button>
          </div>
        </div>
      `;
    }).join("");
  }

  toggleMusicPreview(trackId, streamUrl) {
    if (!this.musicPreviewAudio) return;

    if (this.currentlyPlayingPreviewId === trackId && !this.musicPreviewAudio.paused) {
      this.musicPreviewAudio.pause();
      const btn = document.getElementById(`btnPrev_${trackId}`);
      if (btn) btn.textContent = "▶ Preview";
      this.currentlyPlayingPreviewId = null;
      return;
    }

    if (this.currentlyPlayingPreviewId) {
      const oldBtn = document.getElementById(`btnPrev_${this.currentlyPlayingPreviewId}`);
      if (oldBtn) oldBtn.textContent = "▶ Preview";
    }

    this.currentlyPlayingPreviewId = trackId;
    this.musicPreviewAudio.src = streamUrl;
    this.musicPreviewAudio.currentTime = 0;
    this.musicPreviewAudio.play().then(() => {
      const btn = document.getElementById(`btnPrev_${trackId}`);
      if (btn) btn.textContent = "⏸ Pause";
    }).catch((err) => {
      console.warn("Preview playback error:", err);
    });

    this.musicPreviewAudio.onended = () => {
      const btn = document.getElementById(`btnPrev_${trackId}`);
      if (btn) btn.textContent = "▶ Preview";
      this.currentlyPlayingPreviewId = null;
    };
  }

  async selectOnlineTrack(track) {
    this.closeMusicModal();
    this.closeSpotifyModal();
    if (this.musicPreviewAudio) {
      this.musicPreviewAudio.pause();
      this.musicPreviewAudio.currentTime = 0;
    }
    this.currentTrackTitle = `${track.title} - ${track.artist}`;
    this.logAgent("MusicSelector", `Loading track: "${track.title}" by ${track.artist} (${track.bpm || 120} BPM)...`);

    try {
      const resp = await fetch("/api/music/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          track_id: track.id,
          title: track.title,
          artist: track.artist,
          stream_url: track.stream_url,
          bpm: track.bpm || 120,
          duration: track.duration || 60,
          difficulty: this.currentDifficulty || "normal",
          source: track.source
        })
      });

      const data = await resp.json();
      if (data.status === "success" && data.beatmap) {
        this.currentBeatmap = data.beatmap;
        this.currentTrack = data.stream_url;

        // CRITICAL FIX: Update the actual audio element and the game engine audio
        if (this.audio) {
          this.audio.src = data.stream_url;
          this.audio.currentTime = 0;
          this.audio.load();
        }
        if (this.gameEngine) {
          this.gameEngine.loadBeatmap(data.beatmap);
          if (this.gameEngine.audio) {
            this.gameEngine.audio.src = data.stream_url;
            this.gameEngine.audio.currentTime = 0;
            this.gameEngine.audio.load();
          }
        }

        const sourceLabel = track.source === "jamendo" ? "Jamendo CC" : "Spotify / Pop";
        this.logAgent("RhythmAnalyzer", `✔ Ready to play: "${track.title}" by ${track.artist}! Generated ${data.beatmap.targets.length} targets.`);

        let opt = Array.from(this.trackSelect.options).find(o => o.value === data.stream_url);
        if (!opt) {
          opt = document.createElement("option");
          opt.value = data.stream_url;
          opt.textContent = `🎵 ${track.title} - ${track.artist} (${sourceLabel})`;
          this.trackSelect.appendChild(opt);
        }
        this.trackSelect.value = data.stream_url;
        this.btnStart.disabled = false;

        this.updateNowPlayingBadge(track.title, track.artist);
      }
    } catch (err) {
      this.logAgent("ERROR", `Failed to load track: ${err.message}`);
    }
  }

  updateNowPlayingBadge(title, artist = "") {
    const badge = document.getElementById("nowPlayingBadge");
    const textEl = document.getElementById("nowPlayingText");
    if (badge && textEl) {
      const displayText = artist ? `${title} • ${artist}` : title;
      textEl.textContent = displayText;
      badge.style.display = "inline-flex";
    }
  }

  async testCameraPermission() {
    const btn = document.getElementById("btnRetryWebcam");
    if (btn) btn.textContent = "⏳ Testing Camera...";
    try {
      await this.camera.requestPhysicalCamera();
      this.updateCameraStatus();
      if (btn) btn.textContent = "✅ Camera Connected!";
      this.logAgent("Camera", "Physical webcam successfully connected from Diagnostic Assistant!");
      setTimeout(() => this.closeCamGuideModal(), 1200);
    } catch (err) {
      if (btn) btn.textContent = "❌ Test Failed - See Steps Above";
      this.logAgent("Camera", `Camera test failed: ${err.message}`);
    }
  }

  async saveGameSessionToDatabase(stats) {
    try {
      const playerName = (this.playerNameInput ? this.playerNameInput.value : "").trim() || "Cyber Dancer";
      const trackTitle = this.trackSelect ? this.trackSelect.options[this.trackSelect.selectedIndex]?.text : "FaceBeat Track";
      const difficulty = this.difficultySelect ? this.difficultySelect.value : "normal";

      const payload = {
        player_name: playerName,
        track_title: trackTitle,
        difficulty: difficulty,
        score: stats.score,
        max_combo: stats.maxCombo,
        accuracy: stats.accuracy || 100.0,
        grade: stats.grade || "A",
        perfect_hits: stats.perfectHits || 0,
        great_hits: stats.greatHits || 0,
        good_hits: stats.goodHits || 0,
        misses: stats.misses || 0,
      };

      const res = await fetch("/api/scores/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        this.logAgent("DATABASE", `💾 Session #${data.session_id} saved to SQLite! (Player: ${data.player_name}, Score: ${data.score})`);
      }
    } catch (err) {
      console.warn("[FaceBeatApp] Failed to auto-save score to database:", err);
    }
  }

  async openLeaderboard() {
    if (!this.leaderboardModal) return;
    this.leaderboardModal.style.display = "flex";

    try {
      // 1. Fetch aggregate statistics
      const statsRes = await fetch("/api/scores/stats");
      if (statsRes.ok) {
        const stats = await statsRes.json();
        if (this.statTotalGames) this.statTotalGames.textContent = stats.total_games || "0";
        if (this.statHighScore) this.statHighScore.textContent = (stats.all_time_high_score || 0).toLocaleString();
        if (this.statMaxCombo) this.statMaxCombo.textContent = `${stats.max_combo_record || 0}x`;
      }

      // 2. Fetch top leaderboard records
      const leadRes = await fetch("/api/scores/leaderboard?limit=15");
      if (leadRes.ok) {
        const data = await leadRes.json();
        const rows = data.leaderboard || [];
        if (this.leaderboardBody) {
          if (rows.length === 0) {
            this.leaderboardBody.innerHTML = `<tr><td colspan="6" style="padding: 14px; text-align: center; color: var(--text-muted);">No recorded sessions yet in SQLite. Play a round!</td></tr>`;
          } else {
            this.leaderboardBody.innerHTML = rows
              .map(
                (r, idx) => `
              <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px 12px; font-weight: bold; color: ${idx === 0 ? "#ffd700" : idx === 1 ? "#c0c0c0" : idx === 2 ? "#cd7f32" : "inherit"};">${idx + 1}</td>
                <td style="padding: 10px 12px; font-weight: 600;">${r.player_name}</td>
                <td style="padding: 10px 12px; color: var(--text-muted);">${(r.track_title || "").split("(")[0]}</td>
                <td style="padding: 10px 12px; font-weight: bold; color: var(--accent-cyan);">${(r.score || 0).toLocaleString()}</td>
                <td style="padding: 10px 12px; color: var(--accent-pink);">${r.max_combo}x</td>
                <td style="padding: 10px 12px; font-weight: bold;">${r.grade}</td>
              </tr>
            `
              )
              .join("");
          }
        }
      }
    } catch (err) {
      console.warn("[FaceBeatApp] Failed to load leaderboard:", err);
    }
  }

  closeLeaderboard() {
    if (this.leaderboardModal) {
      this.leaderboardModal.style.display = "none";
    }
  }

  calibrateFace() {
    if (!this.faceTracker) return;
    this.calibrationBanner.style.display = "block";
    this.faceTracker.calibrate();
    this.logAgent("FaceTracker", "Calibrating neutral baseline... Keep face relaxed for 1 sec.");

    setTimeout(() => {
      this.calibrationBanner.style.display = "none";
      this.logAgent("FaceTracker", "Calibration complete! Baseline updated.");
    }, 1200);
  }

  async exportClip() {
    if (!this.lastUploadedVideo) {
      alert("No recorded gameplay session available to export yet. Play a round first!");
      return;
    }

    this.btnExport.disabled = true;
    this.btnExport.textContent = "⏳ Rendering 9:16...";
    this.logAgent("SocialClipper", "Generating TikTok / Instagram Reels 9:16 vertical clip with HUD watermarks...");

    try {
      const playerName = (this.playerNameInput ? this.playerNameInput.value : "").trim() || "Cyber Dancer";
      const res = await fetch("/api/clipper/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_filename: this.lastUploadedVideo,
          score: this.currentScore,
          max_combo: this.maxCombo,
          track_title: this.trackSelect.options[this.trackSelect.selectedIndex].text,
          player_name: playerName,
          audio_filename: this.currentTrack,
        }),
      });

      const data = await res.json();
      if (data.status === "success" && data.clip_url) {
        this.logAgent("SocialClipper", `9:16 Vertical clip rendered: ${data.clip_url}`);
        this.showClipModal(data.clip_url);
      } else {
        throw new Error(data.message || "Failed to render clip.");
      }
    } catch (err) {
      this.logAgent("ERROR", `Failed to export clip: ${err.message}`);
      alert(`Clip render error: ${err.message}`);
    } finally {
      this.btnExport.disabled = false;
      this.btnExport.textContent = "📱 Export 9:16 Clip";
    }
  }

  showClipModal(url) {
    this.clipVideoPlayer.src = url;
    this.btnDownloadClip.href = url;
    this.clipModal.style.display = "flex";
  }

  closeClipModal() {
    this.clipVideoPlayer.pause();
    this.clipModal.style.display = "none";
  }

  closeModal() {
    this.closeClipModal();
  }

  async sendAgentPrompt() {
    const prompt = this.agentPromptInput.value.trim();
    if (!prompt) return;

    this.agentPromptInput.value = "";
    this.logAgent("USER", prompt);

    try {
      const res = await fetch("/api/agents/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      this.logAgent("Orchestrator", data.response);
    } catch (err) {
      this.logAgent("ERROR", `Agent communication error: ${err.message}`);
    }
  }

  logAgent(source, message) {
    if (!this.agentConsole) return;
    const time = new Date().toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const logItem = document.createElement("div");
    logItem.className = "log-item";

    const badgeClass =
      source === "RhythmAnalyzer" ? "badge-rhythm" :
      source === "AudioSafety" ? "badge-safety" :
      source === "SocialClipper" ? "badge-clipper" : "badge-user";

    logItem.innerHTML = `
      <span class="log-time">[${time}]</span>
      <span class="log-badge ${badgeClass}">${source}</span>
      <span class="log-msg">${message}</span>
    `;

    this.agentConsole.appendChild(logItem);
    this.agentConsole.scrollTop = this.agentConsole.scrollHeight;
  }
}

// Bootstrap application on page load
window.addEventListener("DOMContentLoaded", () => {
  window.faceBeatApp = window.app = new FaceBeatApp();
  window.faceBeatApp.initialize();
});
