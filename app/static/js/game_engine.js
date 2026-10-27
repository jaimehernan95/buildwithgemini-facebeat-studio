/**
 * game_engine.js - HTML5 Canvas Rhythm Game Engine with Face Tracking Integration.
 * Renders an active neon highway, hit particle feedback, and ambient idle state.
 */
class GameEngine {
  constructor(canvasId, audioElementId, onStatsUpdate, onGameComplete) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.audio = document.getElementById(audioElementId);
    this.sfxHit = document.getElementById("sfxHit");
    this.onStatsUpdate = onStatsUpdate;
    this.onGameComplete = onGameComplete;
    this.isLooping = true; // Default to continuous groove so song never cuts out abruptly

    if (this.audio) {
      this.audio.onended = () => {
        if (this.isPlaying) {
          if (this.isLooping) {
            this.restartTrackForLoop();
          } else {
            const stats = this.getFinalStats();
            this.stop();
            if (this.onGameComplete) {
              this.onGameComplete(stats);
            }
          }
        }
      };

      this.audio.onerror = (e) => {
        console.error("[GameEngine] Audio element error:", e);
      };

      this.audio.onpause = () => {
        if (this.isPlaying && !this.audio.ended && !this.isLooping) {
          console.warn("[GameEngine] Audio was paused unexpectedly.");
        }
      };
    }

    this.isPlaying = false;
    this.beatmap = null;
    this.targets = [];
    this.particles = [];
    this.floatingTexts = [];

    // Game stats
    this.score = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.perfectHits = 0;
    this.greatHits = 0;
    this.goodHits = 0;
    this.misses = 0;

    // Rhythm layout settings
    this.lanes = {
      left: { x: 420, label: "🤨 BROW [B]", expr: "BrowRaise", color: "#ff007f" },
      center: { x: 640, label: "😮 JAW [SPACE/J]", expr: "MouthOpen", color: "#00f3ff" },
      right: { x: 860, label: "😊 SMILE [S]", expr: "Smile", color: "#ffd700" },
    };

    this.receptorY = 560; // Target hit line
    this.spawnY = 100;
    this.travelTimeMs = 1600; // Duration from spawn to receptor line

    // Current expression inputs from FaceTracker
    this.currentExpressions = { jawOpen: 0, smile: 0, browRaise: 0 };
    this.currentLandmarks = null;

    // Expression activation debounce tracking
    this.lastTriggered = { MouthOpen: 0, Smile: 0, BrowRaise: 0 };

    this.animFrameId = null;
    this.idleAnimFrameId = null;

    // Start idle ambient loop right away so canvas is never blank
    this.startIdleLoop();
  }

  loadBeatmap(beatmapData) {
    this.beatmap = beatmapData;
    this.targets = beatmapData.targets.map((t) => ({
      ...t,
      hit: false,
      missed: false,
    }));
    this.resetStats();
  }

  resetStats() {
    this.score = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.perfectHits = 0;
    this.greatHits = 0;
    this.goodHits = 0;
    this.misses = 0;
    this.particles = [];
    this.floatingTexts = [];
    this.updateStats();
  }

  setLooping(val) {
    this.isLooping = !!val;
    console.log("[GameEngine] Looping mode set to:", this.isLooping);
  }

  restartTrackForLoop() {
    if (!this.audio) return;
    this.audio.currentTime = 0;
    this.audio.play().catch(() => {});
    for (const t of this.targets) {
      t.hit = false;
      t.missed = false;
    }
    this.spawnFloatingText("🔁 LOOP ACTIVE!", this.canvas.width / 2, 220, "#00f3ff");
  }

  updateStats() {
    if (this.onStatsUpdate) {
      const curTime = this.audio ? this.audio.currentTime : 0;
      const totalDur = (this.audio && this.audio.duration && !isNaN(this.audio.duration) && this.audio.duration > 0)
        ? this.audio.duration
        : (this.beatmap ? this.beatmap.duration : 60);

      this.onStatsUpdate({
        score: this.score,
        combo: this.combo,
        maxCombo: this.maxCombo,
        perfectHits: this.perfectHits,
        greatHits: this.greatHits,
        goodHits: this.goodHits,
        misses: this.misses,
        currentTime: curTime,
        duration: totalDur,
        progress: totalDur > 0 ? Math.min(100, (curTime / totalDur) * 100) : 0,
        isLooping: this.isLooping,
      });
    }
  }

  getFinalStats() {
    const totalNotes = this.perfectHits + this.greatHits + this.goodHits + this.misses;
    const accuracy = totalNotes > 0
      ? Math.round(((this.perfectHits * 1.0 + this.greatHits * 0.8 + this.goodHits * 0.5) / totalNotes) * 1000) / 10
      : 100.0;
    let grade = "C";
    if (accuracy >= 95) grade = "S";
    else if (accuracy >= 85) grade = "A";
    else if (accuracy >= 70) grade = "B";

    return {
      score: this.score,
      maxCombo: this.maxCombo,
      accuracy,
      grade,
      perfectHits: this.perfectHits,
      greatHits: this.greatHits,
      goodHits: this.goodHits,
      misses: this.misses,
    };
  }

  start() {
    if (!this.beatmap) return;
    this.isPlaying = true;
    if (this.idleAnimFrameId) {
      cancelAnimationFrame(this.idleAnimFrameId);
      this.idleAnimFrameId = null;
    }
    this.audio.currentTime = 0;
    this.audio.play().catch(() => {});
    this.loop();
  }

  stop() {
    this.isPlaying = false;
    if (this.audio) this.audio.pause();
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    this.startIdleLoop();
  }

  startIdleLoop() {
    if (this.idleAnimFrameId) return;
    const idleRender = (time) => {
      if (!this.isPlaying) {
        this.renderIdle(time);
        this.idleAnimFrameId = requestAnimationFrame(idleRender);
      }
    };
    this.idleAnimFrameId = requestAnimationFrame(idleRender);
  }

  updateExpressions(expressions, landmarks) {
    this.currentExpressions = expressions;
    this.currentLandmarks = landmarks;

    if (this.isPlaying) {
      this.checkExpressionHits();
    }
  }

  checkExpressionHits() {
    const currentAudioMs = this.audio.currentTime * 1000;
    const now = performance.now();

    const exprMap = {
      MouthOpen: this.currentExpressions.jawOpen,
      Smile: this.currentExpressions.smile,
      BrowRaise: this.currentExpressions.browRaise,
    };

    const threshold = 0.45;

    for (const [exprName, value] of Object.entries(exprMap)) {
      if (value > threshold && now - this.lastTriggered[exprName] > 220) {
        this.lastTriggered[exprName] = now;
        this.attemptHitTarget(exprName, currentAudioMs);
      }
    }
  }

  attemptHitTarget(exprName, currentAudioMs) {
    let closestTarget = null;
    let minDiff = Infinity;

    for (const target of this.targets) {
      if (target.hit || target.missed) continue;
      if (target.expression !== exprName) continue;

      const diff = Math.abs(currentAudioMs - target.time_ms);
      if (diff < minDiff && diff <= 240) {
        minDiff = diff;
        closestTarget = target;
      }
    }

    if (!closestTarget) return;

    closestTarget.hit = true;
    const lane = this.lanes[closestTarget.lane] || this.lanes.center;

    let rating = "GOOD";
    let pts = 50;
    let color = "#10b981";

    if (minDiff <= 75) {
      rating = "PERFECT!";
      pts = 100;
      color = "#ffd700";
      this.perfectHits++;
    } else if (minDiff <= 140) {
      rating = "GREAT!";
      pts = 75;
      color = "#00f3ff";
      this.greatHits++;
    } else {
      this.goodHits++;
    }

    this.combo++;
    if (this.combo > this.maxCombo) this.maxCombo = this.combo;

    const multiplier = 1 + Math.floor(this.combo / 10) * 0.5;
    this.score += Math.round(pts * multiplier);

    if (this.sfxHit) {
      this.sfxHit.currentTime = 0;
      this.sfxHit.play().catch(() => {});
    }

    this.spawnParticles(lane.x, this.receptorY, color);
    this.spawnFloatingText(rating, lane.x, this.receptorY - 30, color);
    this.updateStats();
  }

  spawnParticles(x, y, color) {
    for (let i = 0; i < 18; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = Math.random() * 5 + 2;
      this.particles.push({
        x: x,
        y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1.0,
        decay: Math.random() * 0.04 + 0.03,
        color: color,
        size: Math.random() * 5 + 3,
      });
    }
  }

  spawnFloatingText(text, x, y, color) {
    this.floatingTexts.push({
      text: text,
      x: x,
      y: y,
      vy: -1.8,
      life: 1.0,
      color: color,
    });
  }

  loop() {
    if (!this.isPlaying) return;

    this.render();

    // Periodically update progress clock
    if (Math.random() < 0.25) {
      this.updateStats();
    }

    if (this.audio.ended || (this.audio.duration > 0 && this.audio.currentTime >= this.audio.duration - 0.1)) {
      if (this.isLooping) {
        this.restartTrackForLoop();
      } else {
        const stats = this.getFinalStats();
        this.stop();
        if (this.onGameComplete) {
          this.onGameComplete(stats);
        }
        return;
      }
    }

    this.animFrameId = requestAnimationFrame(() => this.loop());
  }

  renderIdle(time = 0) {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const pulse = Math.sin(time * 0.003) * 0.5 + 0.5;

    ctx.clearRect(0, 0, w, h);

    // Draw subtle landmarks
    this.renderLandmarks(ctx, w, h);

    // Draw lanes and receptors
    this.renderLanes(ctx, h, pulse);

    // Idle Ready Prompt
    ctx.save();
    ctx.fillStyle = `rgba(0, 243, 255, ${0.7 + pulse * 0.3})`;
    ctx.font = "bold 22px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.shadowColor = "#00f3ff";
    ctx.shadowBlur = 12;
    ctx.fillText("READY TO PLAY - CLICK [▶ START GAME]", w / 2, 280);

    ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
    ctx.font = "14px Inter, sans-serif";
    ctx.shadowBlur = 0;
    ctx.fillText("Test expressions below with buttons or [Space/J], [S], [B] keys", w / 2, 315);
    ctx.restore();
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const currentAudioMs = this.audio.currentTime * 1000;

    ctx.clearRect(0, 0, w, h);

    // 1. Draw subtle landmarks
    this.renderLandmarks(ctx, w, h);

    // 2. Draw Lanes & Receptors
    this.renderLanes(ctx, h, 1.0);

    // 3. Update & Render Moving Targets
    for (const target of this.targets) {
      if (target.hit || target.missed) continue;

      const timeDiff = target.time_ms - currentAudioMs;

      if (timeDiff < -240) {
        target.missed = true;
        this.combo = 0;
        this.misses++;
        const lane = this.lanes[target.lane] || this.lanes.center;
        this.spawnFloatingText("MISS", lane.x, this.receptorY, "#ef4444");
        this.updateStats();
        continue;
      }

      if (timeDiff > this.travelTimeMs || timeDiff < -300) continue;

      const progress = 1.0 - timeDiff / this.travelTimeMs;
      const targetY = this.spawnY + progress * (this.receptorY - this.spawnY);
      const lane = this.lanes[target.lane] || this.lanes.center;

      ctx.fillStyle = lane.color;
      ctx.shadowColor = lane.color;
      ctx.shadowBlur = 20;

      ctx.beginPath();
      ctx.arc(lane.x, targetY, 28, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(lane.x, targetY, 12, 0, Math.PI * 2);
      ctx.fill();

      ctx.shadowBlur = 0;
    }

    // 4. Update & Render Particles
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.life -= p.decay;

      if (p.life <= 0) {
        this.particles.splice(i, 1);
        continue;
      }

      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.life;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1.0;
    }

    // 5. Update & Render Floating Text
    for (let i = this.floatingTexts.length - 1; i >= 0; i--) {
      const ft = this.floatingTexts[i];
      ft.y += ft.vy;
      ft.life -= 0.025;

      if (ft.life <= 0) {
        this.floatingTexts.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.fillStyle = ft.color;
      ctx.globalAlpha = ft.life;
      ctx.font = "900 24px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.shadowColor = ft.color;
      ctx.shadowBlur = 10;
      ctx.fillText(ft.text, ft.x, ft.y);
      ctx.restore();
    }
  }

  renderLanes(ctx, h, pulseScale = 1.0) {
    for (const [key, lane] of Object.entries(this.lanes)) {
      // Highway track
      ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(lane.x, this.spawnY);
      ctx.lineTo(lane.x, h);
      ctx.stroke();

      // Receptor circle
      ctx.strokeStyle = lane.color;
      ctx.lineWidth = 3;
      ctx.shadowColor = lane.color;
      ctx.shadowBlur = 12 * pulseScale;
      ctx.beginPath();
      ctx.arc(lane.x, this.receptorY, 36, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Receptor label
      ctx.fillStyle = lane.color;
      ctx.font = "bold 13px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(lane.label, lane.x, this.receptorY + 54);
    }
  }

  renderLandmarks(ctx, w, h) {
    if (this.currentLandmarks) {
      ctx.fillStyle = "rgba(0, 243, 255, 0.4)";
      for (let i = 0; i < this.currentLandmarks.length; i += 6) {
        const p = this.currentLandmarks[i];
        const px = (1.0 - p.x) * w;
        const py = p.y * h;
        ctx.beginPath();
        ctx.arc(px, py, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

window.GameEngine = GameEngine;
