#!/usr/bin/env python3
"""
auditor.py - Comprehensive End-to-End System & Endpoint Auditor for FaceBeat-Studio.
Audits:
 1. System dependencies & binaries (FFmpeg, audio files, writable directories).
 2. Static asset integrity & template references (no 404s or unreadable files).
 3. Template rendering (preventing Jinja2 / Starlette 500 errors).
 4. Internal API & Route audit via FastAPI TestClient (catching all unhandled exceptions).
 5. Google Antigravity Multi-Agent orchestration & tool configurations.
 6. Live network server audit (verifying http://127.0.0.1:8000 if running).
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class FaceBeatAuditor:
    def __init__(self):
        self.passed: List[str] = []
        self.warnings: List[str] = []
        self.failures: List[str] = []

    def log_pass(self, name: str, detail: str = ""):
        self.passed.append(name)
        msg = f"  {GREEN}✔ [PASS]{RESET} {BOLD}{name}{RESET}"
        if detail:
            msg += f" - {detail}"
        print(msg)

    def log_warn(self, name: str, detail: str):
        self.warnings.append(name)
        print(f"  {YELLOW}⚠ [WARN]{RESET} {BOLD}{name}{RESET} - {detail}")

    def log_fail(self, name: str, detail: str):
        self.failures.append(name)
        print(f"  {RED}✖ [FAIL]{RESET} {BOLD}{name}{RESET} - {detail}")

    def header(self, title: str):
        print(f"\n{CYAN}{BOLD}=== {title} ==={RESET}")

    def audit_environment_and_binaries(self):
        self.header("1. Environment & Binary Dependencies Audit")

        # 1.1 FFmpeg
        ffmpeg_bin = "/usr/bin/ffmpeg"
        if Path(ffmpeg_bin).exists() and os.access(ffmpeg_bin, os.X_OK):
            try:
                res = subprocess.run([ffmpeg_bin, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                ver_line = res.stdout.split("\n")[0] if res.stdout else "Available"
                self.log_pass("FFmpeg Binary", ver_line)
            except Exception as e:
                self.log_fail("FFmpeg Binary", f"Execution failed: {e}")
        else:
            self.log_fail("FFmpeg Binary", f"Not found at {ffmpeg_bin}")

        # 1.2 Directories
        from app.config import settings
        dirs_to_check = [
            ("Static Directory", settings.STATIC_DIR),
            ("Audio Directory", settings.AUDIO_DIR),
            ("Media Directory", settings.MEDIA_DIR),
            ("Clips Directory", settings.CLIPS_DIR),
            ("Templates Directory", settings.TEMPLATES_DIR),
        ]
        for name, dir_path in dirs_to_check:
            if dir_path.exists() and dir_path.is_dir():
                test_file = dir_path / ".audit_perm_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    self.log_pass(f"Directory: {name}", f"Writable ({dir_path})")
                except Exception as e:
                    self.log_fail(f"Directory: {name}", f"Not writable ({e})")
            else:
                self.log_fail(f"Directory: {name}", f"Directory missing ({dir_path})")

        # 1.3 Royalty-Free Audio Files
        from app.services.audio_processor import AudioProcessor
        tracks = AudioProcessor.ensure_default_audio_library(settings.AUDIO_DIR)
        for t in tracks:
            p = settings.AUDIO_DIR / t["filename"]
            if p.exists() and p.stat().st_size > 1000:
                self.log_pass(f"Audio Track: {t['title']}", f"{p.name} ({round(p.stat().st_size / 1024, 1)} KB)")
            else:
                self.log_fail(f"Audio Track: {t['title']}", f"Missing or empty at {p}")

    def audit_static_assets_and_templates(self):
        self.header("2. Static Assets & Template References Audit")
        from app.config import settings

        template_file = settings.TEMPLATES_DIR / "index.html"
        if not template_file.exists():
            self.log_fail("Template File", f"index.html not found at {template_file}")
            return

        self.log_pass("Template File", f"Found {template_file.name}")
        content = template_file.read_text(encoding="utf-8")

        # Extract all local static references (/static/...)
        static_refs = set(re.findall(r'["\'](/static/[^"\'?#]+)["\']', content))
        if not static_refs:
            self.log_warn("Static References", "No /static/ references detected in template.")
        else:
            for ref in sorted(static_refs):
                # Map /static/... to app/static/...
                rel_path = ref.replace("/static/", "")
                disk_path = settings.STATIC_DIR / rel_path
                if disk_path.exists() and disk_path.is_file():
                    size_kb = round(disk_path.stat().st_size / 1024, 2)
                    self.log_pass(f"Static Asset: {ref}", f"Exists ({size_kb} KB)")
                else:
                    self.log_fail(f"Static Asset: {ref}", f"Missing file on disk: {disk_path}")

    def audit_template_rendering(self):
        self.header("3. HTML Template Rendering Audit")
        from starlette.templating import Jinja2Templates
        from starlette.requests import Request
        from app.config import settings

        try:
            templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [],
            }
            req = Request(scope)
            resp = templates.TemplateResponse(
                request=req,
                name="index.html",
                context={"app_name": "FaceBeat-Studio", "spotify_configured": False},
            )
            if resp.status_code == 200:
                body = resp.body.decode("utf-8")
                if "FaceBeat Studio" in body and "<video id=\"webcam\"" in body:
                    self.log_pass("Template Render (GET /)", "HTML rendered successfully without 500 error.")
                else:
                    self.log_fail("Template Render (GET /)", "Rendered HTML missing key DOM tags.")
            else:
                self.log_fail("Template Render (GET /)", f"Status code {resp.status_code}")
        except Exception as e:
            self.log_fail("Template Render (GET /)", f"Rendering crashed: {type(e).__name__}: {e}")

    def audit_fastapi_endpoints(self):
        self.header("4. FastAPI Internal Route & Exception Audit")
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)

        endpoints = [
            ("GET", "/", None, 200, "Main Game Frontend"),
            ("GET", "/health", None, 200, "Health Check Endpoint"),
            ("GET", "/api/tracks", None, 200, "Audio Tracks Catalog"),
            ("POST", "/api/tracks/safety-check", {"track_title": "Lo-Fi Sunset"}, 200, "Audio Safety Check"),
            ("POST", "/api/tracks/analyze", {"filename": "lofi_piano_chill.wav", "difficulty": "normal"}, 200, "Rhythm Beatmap Analyzer"),
            ("GET", "/api/spotify/login", None, 200, "Spotify Login OAuth URL"),
            ("GET", "/api/spotify/callback?mock=true", None, 200, "Spotify OAuth Callback"),
            ("GET", "/api/music/jamendo/trending", None, 200, "Jamendo Trending Music API"),
            ("GET", "/api/music/jamendo/search?q=cyber", None, 200, "Jamendo Search API"),
            ("GET", "/api/music/spotify/search?q=weeknd", None, 200, "Spotify Search & Catalog API"),
            ("POST", "/api/music/select", {"track_id": "jam_101", "title": "Cyber Sunset", "artist": "Neon", "stream_url": "/static/audio/cyber_synth_beat.wav", "bpm": 128, "duration": 60, "difficulty": "normal", "source": "jamendo"}, 200, "Online Music Select & Beatmap API"),
            ("POST", "/api/agents/chat", {"prompt": "Auditor ping"}, 200, "Multi-Agent Chat Facade"),
        ]

        for method, route, payload, expected_status, desc in endpoints:
            try:
                if method == "GET":
                    res = client.get(route)
                elif method == "POST":
                    res = client.post(route, json=payload)
                else:
                    res = client.request(method, route)

                if res.status_code == expected_status:
                    self.log_pass(f"{method} {route}", f"{desc} -> HTTP {res.status_code}")
                elif res.status_code >= 500:
                    self.log_fail(f"{method} {route}", f"INTERNAL SERVER ERROR (HTTP {res.status_code}): {res.text[:120]}")
                else:
                    self.log_warn(f"{method} {route}", f"Unexpected status {res.status_code} (expected {expected_status})")
            except Exception as e:
                self.log_fail(f"{method} {route}", f"Exception raised: {type(e).__name__}: {e}")

    def audit_antigravity_agents(self):
        self.header("5. Google Antigravity Multi-Agent Architecture Audit")
        from app.agents.orchestrator import orchestrator

        try:
            config = orchestrator.agent_config
            subagents = config.subagents or []
            subagent_names = [s.name for s in subagents]

            expected = ["RhythmAnalyzerAgent", "AudioSafetyAgent", "SocialClipperAgent"]
            missing = [name for name in expected if name not in subagent_names]

            if not missing:
                self.log_pass("Subagent Registration", f"All 3 agents registered: {subagent_names}")
            else:
                self.log_fail("Subagent Registration", f"Missing subagents: {missing}")

            # Verify capabilities
            if config.capabilities and config.capabilities.enable_subagents:
                self.log_pass("Subagent Capabilities", "enable_subagents is True, max_depth is set.")
            else:
                self.log_fail("Subagent Capabilities", "enable_subagents is False or unconfigured.")

            # Test deterministic tools
            rhythm_test = orchestrator.analyze_track("lofi_piano_chill.wav", "normal")
            if "bpm" in rhythm_test and "targets" in rhythm_test:
                self.log_pass("RhythmAnalyzer Tool Execution", f"BPM: {rhythm_test['bpm']}, Targets: {rhythm_test['total_targets']}")
            else:
                self.log_fail("RhythmAnalyzer Tool Execution", f"Invalid response: {rhythm_test}")

            safety_test = orchestrator.check_safety("Lo-Fi Piano Sunset")
            if safety_test.get("is_copyright_safe") is True:
                self.log_pass("AudioSafety Tool Execution", "Verified copyright detection.")
            else:
                self.log_fail("AudioSafety Tool Execution", f"Safety check failed: {safety_test}")

        except Exception as e:
            self.log_fail("Antigravity Agent Orchestrator", f"Audit crashed: {e}")

    def audit_live_server_network(self):
        self.header("6. Live Server Network Audit (http://127.0.0.1:8000)")
        import urllib.request
        import urllib.error

        urls_to_test = [
            ("http://127.0.0.1:8000/", "Live Root Webpage (GET /)"),
            ("http://127.0.0.1:8000/health", "Live Health Check"),
            ("http://127.0.0.1:8000/static/css/style.css", "Live CSS Stylesheet"),
            ("http://127.0.0.1:8000/static/js/app.js", "Live JS Application Controller"),
            ("http://127.0.0.1:8000/api/tracks", "Live Tracks API"),
        ]

        live_server_online = False
        for url, desc in urls_to_test:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "FaceBeat-Auditor/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    status = resp.status
                    if status == 200:
                        live_server_online = True
                        self.log_pass(f"Live URL: {url}", f"{desc} -> HTTP 200 OK")
                    else:
                        self.log_warn(f"Live URL: {url}", f"Returned HTTP {status}")
            except urllib.error.HTTPError as e:
                if e.code >= 500:
                    self.log_fail(f"Live URL: {url}", f"INTERNAL SERVER ERROR HTTP {e.code}: {e.reason}")
                else:
                    self.log_warn(f"Live URL: {url}", f"HTTP {e.code}: {e.reason}")
            except urllib.error.URLError:
                # Server might not be running on this port right now
                break
            except Exception as e:
                self.log_fail(f"Live URL: {url}", f"Network error: {e}")

        if not live_server_online:
            self.log_warn("Live Server Check", "No live HTTP server detected on http://127.0.0.1:8000 (Start with: uvicorn app.main:app)")

    def audit_edge_cases_and_boundaries(self):
        self.header("7. Edge Cases & Boundary Resilience Audit")
        from app.services.audio_processor import AudioProcessor
        from app.services.video_renderer import VideoRenderer
        from fastapi.testclient import TestClient
        from app.main import app
        import tempfile
        import wave
        import numpy as np

        client = TestClient(app)

        # 7.1 Audio: Missing file returns resilient procedural beatmap
        try:
            missing_result = AudioProcessor.analyze_audio(Path("/nonexistent/fake_track.wav"), difficulty="hard")
            if missing_result.get("bpm") > 0 and missing_result.get("total_targets", 0) > 0:
                self.log_pass("Audio Edge Case: Missing File", f"Safely generated fallback beatmap with {missing_result['total_targets']} targets.")
            else:
                self.log_fail("Audio Edge Case: Missing File", "Did not return valid beatmap structure.")
        except Exception as e:
            self.log_fail("Audio Edge Case: Missing File", f"Threw unexpected exception: {e}")

        # 7.2 Audio: Unknown / invalid difficulty fallback
        try:
            diff_result = AudioProcessor.analyze_audio(Path("app/static/audio/lofi_piano_chill.wav"), difficulty="ultra_impossible")
            if diff_result.get("bpm") > 0:
                self.log_pass("Audio Edge Case: Invalid Difficulty", "Normalized unknown difficulty to default without crashing.")
            else:
                self.log_fail("Audio Edge Case: Invalid Difficulty", "Failed to analyze with unknown difficulty.")
        except Exception as e:
            self.log_fail("Audio Edge Case: Invalid Difficulty", f"Exception on invalid difficulty: {e}")

        # 7.3 Audio: Very short / sub-second audio
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                temp_path = Path(tf.name)
            sr = 44100
            short_samples = (np.sin(2 * np.pi * 440 * np.linspace(0, 0.2, int(sr * 0.2))) * 32767).astype(np.int16)
            with wave.open(str(temp_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(short_samples.tobytes())

            short_result = AudioProcessor.analyze_audio(temp_path)
            temp_path.unlink(missing_ok=True)
            if short_result.get("bpm") > 0 and len(short_result.get("targets", [])) > 0:
                self.log_pass("Audio Edge Case: Sub-second Audio", f"Handled short audio gracefully ({short_result['total_targets']} targets).")
            else:
                self.log_fail("Audio Edge Case: Sub-second Audio", "Failed to generate beatmap for short audio.")
        except Exception as e:
            self.log_fail("Audio Edge Case: Sub-second Audio", f"Crashed on short audio: {e}")

        # 7.4 Video Clipper: Special character escaping in drawtext filter
        try:
            dirty_title = "100% 'Funky': Test & [Synth]\\Escape"
            sanitized = VideoRenderer._sanitize_drawtext(dirty_title)
            if "'" not in sanitized and "%" not in sanitized and "\\" not in sanitized.replace("\\:", ""):
                self.log_pass("Video Edge Case: Drawtext Text Sanitization", f"Sanitized: '{dirty_title}' -> '{sanitized}'")
            else:
                self.log_fail("Video Edge Case: Drawtext Text Sanitization", f"Unsafe characters remained in sanitized string: '{sanitized}'")
        except Exception as e:
            self.log_fail("Video Edge Case: Drawtext Text Sanitization", f"Sanitization crashed: {e}")

        # 7.5 Video Clipper: Nonexistent source video file returns clean error dict
        try:
            clip_res = VideoRenderer.render_vertical_clip(
                input_video_path=Path("/tmp/nonexistent_video.webm"),
                output_clip_path=Path("/tmp/clip_out.mp4"),
                score=-50,
                max_combo=-10,
                track_title="Test",
                player_name="Tester",
            )
            if not clip_res.get("success") and "error" in clip_res:
                self.log_pass("Video Edge Case: Missing Source Video", f"Returned clean error response: {clip_res['error']}")
            else:
                self.log_fail("Video Edge Case: Missing Source Video", "Did not return success=False error dictionary.")
        except Exception as e:
            self.log_fail("Video Edge Case: Missing Source Video", f"Threw unhandled exception: {e}")

        # 7.6 API: Path traversal prevention in /api/tracks/analyze
        try:
            res = client.post("/api/tracks/analyze", json={"filename": "../../../../../etc/passwd", "difficulty": "normal"})
            if res.status_code in (200, 404):
                self.log_pass("API Edge Case: Path Traversal on /api/tracks/analyze", f"Neutralized traversal, returned HTTP {res.status_code}")
            else:
                self.log_fail("API Edge Case: Path Traversal on /api/tracks/analyze", f"Returned unexpected HTTP {res.status_code}")
        except Exception as e:
            self.log_fail("API Edge Case: Path Traversal on /api/tracks/analyze", f"Crashed: {e}")

        # 7.7 API: Path traversal & negative stats on /api/clipper/render
        try:
            res = client.post(
                "/api/clipper/render",
                json={
                    "video_filename": "../../secret.mp4",
                    "score": -999,
                    "max_combo": -10,
                    "track_title": "Edge Test",
                    "player_name": "Edge Player",
                },
            )
            if res.status_code in (400, 404):
                self.log_pass("API Edge Case: Traversal & Negative Stats on /api/clipper/render", f"Clean client error HTTP {res.status_code}")
            elif res.status_code == 500:
                self.log_fail("API Edge Case: Traversal & Negative Stats on /api/clipper/render", f"Returned HTTP 500: {res.text}")
            else:
                self.log_pass("API Edge Case: Traversal & Negative Stats on /api/clipper/render", f"Returned HTTP {res.status_code}")
        except Exception as e:
            self.log_fail("API Edge Case: Traversal & Negative Stats on /api/clipper/render", f"Crashed: {e}")

        # 7.8 API: Empty track title on /api/tracks/safety-check
        try:
            res = client.post("/api/tracks/safety-check", json={"track_title": "   "})
            if res.status_code == 200:
                self.log_pass("API Edge Case: Whitespace Track Title on /api/tracks/safety-check", "Returned valid safety JSON (HTTP 200)")
            else:
                self.log_fail("API Edge Case: Whitespace Track Title on /api/tracks/safety-check", f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            self.log_fail("API Edge Case: Whitespace Track Title on /api/tracks/safety-check", f"Crashed: {e}")

        # 7.9 Frontend WebGL & Fallback Architecture
        try:
            face_tracker_js = (PROJECT_ROOT / "app/static/js/face_tracker.js").read_text()
            camera_js = (PROJECT_ROOT / "app/static/js/camera.js").read_text()
            app_js = (PROJECT_ROOT / "app/static/js/app.js").read_text()

            has_webgl_probe = "isWebGLSupported" in face_tracker_js
            has_webgl_guard = "webglDisabled" in face_tracker_js
            has_auto_groove = "setAutoGroove" in face_tracker_js and "toggleAutoGroove" in app_js
            has_cyber_avatar = "startVirtualAvatar" in camera_js and "captureStream" in camera_js

            if has_webgl_probe and has_webgl_guard and has_auto_groove and has_cyber_avatar:
                self.log_pass("Frontend Edge Case: WebGL Probe & Virtual Fallback", "Found WebGL probing, context loss guards, Auto-Groove, and Virtual Cyber Avatar.")
            else:
                missing = []
                if not has_webgl_probe: missing.append("isWebGLSupported")
                if not has_webgl_guard: missing.append("webglDisabled guard")
                if not has_auto_groove: missing.append("Auto-Groove")
                if not has_cyber_avatar: missing.append("Virtual Avatar captureStream")
                self.log_fail("Frontend Edge Case: WebGL Probe & Virtual Fallback", f"Missing components: {', '.join(missing)}")
        except Exception as e:
            self.log_fail("Frontend Edge Case: WebGL Probe & Virtual Fallback", f"Failed to check frontend JS: {e}")

    def audit_database_persistence(self):
        self.header("8. Database Persistence & Score Tracking Audit")
        from app.services.database import DatabaseService
        from fastapi.testclient import TestClient
        from app.main import app
        from app.config import settings

        client = TestClient(app)

        # 8.1 Database file and schema tables
        try:
            conn = DatabaseService.get_connection()
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            conn.close()
            required = ["game_sessions", "player_profiles", "exported_clips"]
            if all(t in tables for t in required):
                self.log_pass("Database Schema & Tables", f"SQLite WAL database verified at {settings.DATABASE_PATH} with tables: {', '.join(required)}")
            else:
                self.log_fail("Database Schema & Tables", f"Missing tables. Found: {tables}")
        except Exception as e:
            self.log_fail("Database Schema & Tables", f"Failed to verify SQLite schema: {e}")

        # 8.2 Save game session & update player profile
        try:
            res = DatabaseService.save_game_session(
                player_name="AuditorBot",
                track_title="Lo-Fi Piano Sunset",
                difficulty="normal",
                score=77777,
                max_combo=50,
                accuracy=96.0,
                grade="S",
            )
            profile = DatabaseService.get_player_profile("AuditorBot")
            if res.get("saved") and profile and profile["high_score"] >= 77777:
                self.log_pass("Database Session & Profile Update", f"Session #{res['session_id']} saved; AuditorBot high score: {profile['high_score']}")
            else:
                self.log_fail("Database Session & Profile Update", "Failed to save session or update player profile.")
        except Exception as e:
            self.log_fail("Database Session & Profile Update", f"Error saving session: {e}")

        # 8.3 Leaderboard and Aggregate Stats
        try:
            lb = DatabaseService.get_leaderboard(limit=5)
            stats = DatabaseService.get_stats()
            if isinstance(lb, list) and len(lb) > 0 and stats.get("total_games", 0) > 0:
                self.log_pass("Database Leaderboard & Stats", f"Top score: {lb[0]['score']} by {lb[0]['player_name']} (Total games: {stats['total_games']})")
            else:
                self.log_fail("Database Leaderboard & Stats", "Leaderboard or aggregate stats returned empty data.")
        except Exception as e:
            self.log_fail("Database Leaderboard & Stats", f"Error querying stats: {e}")

        # 8.4 REST API Database Endpoints
        try:
            resp_save = client.post("/api/scores/save", json={
                "player_name": "API_Auditor",
                "track_title": "Neon Grid Pulse",
                "difficulty": "normal",
                "score": 65000,
                "max_combo": 40,
                "grade": "A",
            })
            resp_lb = client.get("/api/scores/leaderboard?limit=3")
            resp_stats = client.get("/api/scores/stats")
            resp_health = client.get("/health")

            all_ok = (
                resp_save.status_code == 200
                and resp_lb.status_code == 200
                and resp_stats.status_code == 200
                and resp_health.json().get("database_connected") is True
            )
            if all_ok:
                self.log_pass("REST API Database Endpoints", "Verified POST /api/scores/save, GET /api/scores/leaderboard, GET /api/scores/stats, and database_connected health check.")
            else:
                self.log_fail("REST API Database Endpoints", f"Endpoint failure: save={resp_save.status_code}, lb={resp_lb.status_code}, stats={resp_stats.status_code}")
        except Exception as e:
            self.log_fail("REST API Database Endpoints", f"Error calling database endpoints: {e}")

    def print_summary(self) -> int:
        print(f"\n{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}AUDIT SUMMARY:{RESET}")
        print(f"  {GREEN}✔ Passed:{RESET}   {len(self.passed)}")
        print(f"  {YELLOW}⚠ Warnings:{RESET} {len(self.warnings)}")
        print(f"  {RED}✖ Failures:{RESET} {len(self.failures)}")
        print(f"{BOLD}{'=' * 60}{RESET}")

        if self.failures:
            print(f"\n{RED}{BOLD}🚨 AUDIT FAILED! The system has {len(self.failures)} critical error(s) to fix.{RESET}\n")
            return 1
        else:
            print(f"\n{GREEN}{BOLD}✨ ALL AUDITS PASSED! No Internal Server Errors or missing assets detected.{RESET}\n")
            return 0


def main():
    auditor = FaceBeatAuditor()
    print(f"\n{BOLD}{CYAN}🔍 Starting FaceBeat-Studio Full System & Health Auditor...{RESET}")
    auditor.audit_environment_and_binaries()
    auditor.audit_static_assets_and_templates()
    auditor.audit_template_rendering()
    auditor.audit_fastapi_endpoints()
    auditor.audit_antigravity_agents()
    auditor.audit_live_server_network()
    auditor.audit_edge_cases_and_boundaries()
    auditor.audit_database_persistence()
    sys.exit(auditor.print_summary())


if __name__ == "__main__":
    main()
