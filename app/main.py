import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.agents.orchestrator import orchestrator
from app.services.audio_processor import AudioProcessor
from app.services.spotify_service import SpotifyService
from app.services.jamendo_service import JamendoService
from app.services.database import DatabaseService

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Interactive Face-Tracking Rhythm Game powered by Google Antigravity",
    version="1.0.0",
)

# Ensure runtime directories
settings.ensure_directories()
AudioProcessor.ensure_default_audio_library(settings.AUDIO_DIR)
DatabaseService.init_db()

# Mount Static Files and Templates
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


# Pydantic Request Models
class AnalyzeRequest(BaseModel):
    filename: str
    difficulty: str = "normal"


class SafetyCheckRequest(BaseModel):
    track_title: str
    artist: str = ""


class ChatRequest(BaseModel):
    prompt: str


class RenderClipRequest(BaseModel):
    video_filename: str
    score: int = 0
    max_combo: int = 0
    track_title: str = "FaceBeat Jam"
    player_name: str = "Player"
    audio_filename: str = ""


class MusicSelectRequest(BaseModel):
    track_id: str
    title: str
    artist: str = ""
    stream_url: str
    bpm: float = 120.0
    duration: float = 60.0
    difficulty: str = "normal"
    source: str = "jamendo"


class SaveScoreRequest(BaseModel):
    player_name: str = "Cyber Dancer"
    track_title: str = "Lo-Fi Piano Sunset"
    difficulty: str = "normal"
    score: int = 0
    max_combo: int = 0
    accuracy: float = 100.0
    grade: str = "A"
    perfect_hits: int = 0
    great_hits: int = 0
    good_hits: int = 0
    misses: int = 0


# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Renders the main game interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "spotify_configured": SpotifyService.is_configured(),
        },
    )


@app.get("/api/tracks")
async def get_available_tracks():
    """Lists all available safe tracks and audio presets."""
    try:
        catalog = orchestrator.get_safe_tracks()
        return catalog
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tracks/analyze")
async def analyze_track_endpoint(req: AnalyzeRequest):
    """Analyzes audio frequency peaks and generates beatmap targets using RhythmAnalyzerAgent."""
    try:
        clean_filename = Path(req.filename).name if req.filename else "lofi_piano_chill.wav"
        result = orchestrator.analyze_track(clean_filename, difficulty=req.difficulty)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tracks/safety-check")
async def check_safety_endpoint(req: SafetyCheckRequest):
    """Audits track copyright safety and advises on DMCA risk via AudioSafetyAgent."""
    try:
        title = (req.track_title or "").strip()
        return orchestrator.check_safety(title, artist=req.artist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/spotify/login")
async def spotify_login():
    """Returns or redirects to Spotify OAuth authorization URL."""
    auth_url = SpotifyService.get_authorization_url()
    return {"auth_url": auth_url, "configured": SpotifyService.is_configured()}


@app.get("/api/spotify/callback")
async def spotify_callback(code: Optional[str] = None, mock: Optional[bool] = False):
    """Handles Spotify authorization code exchange."""
    if mock or not code:
        token_info = SpotifyService.exchange_code_for_token("demo_code")
    else:
        token_info = SpotifyService.exchange_code_for_token(code)
    return JSONResponse(content=token_info)


@app.get("/api/music/jamendo/search")
async def jamendo_search_endpoint(q: str = "", limit: int = 10):
    """Searches royalty-free Creative Commons tracks on Jamendo."""
    try:
        results = JamendoService.search_tracks(query=q, limit=limit)
        return {"query": q, "count": len(results), "tracks": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/music/jamendo/trending")
async def jamendo_trending_endpoint(limit: int = 10):
    """Retrieves trending/recommended Creative Commons tracks from Jamendo."""
    try:
        results = JamendoService.get_trending_tracks(limit=limit)
        return {"count": len(results), "tracks": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/music/spotify/search")
async def spotify_search_endpoint(q: str = "", limit: int = 10):
    """Searches tracks, metadata, and BPM using Spotify Web API (or curated hits)."""
    try:
        results = SpotifyService.search_tracks(query=q, limit=limit)
        return {"query": q, "count": len(results), "configured": SpotifyService.is_configured(), "tracks": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/music/select")
async def music_select_endpoint(req: MusicSelectRequest):
    """Selects an online track and generates a synchronized procedural beatmap."""
    try:
        bpm = float(req.bpm) if req.bpm and req.bpm > 40 else 120.0
        duration = float(req.duration) if req.duration and req.duration > 5 else 60.0
        difficulty = req.difficulty.lower() if req.difficulty in ("easy", "normal", "hard") else "normal"

        beatmap = AudioProcessor.generate_procedural_beatmap(
            bpm=bpm,
            duration_sec=duration,
            difficulty=difficulty
        )

        return {
            "status": "success",
            "track_id": req.track_id,
            "title": req.title,
            "artist": req.artist,
            "stream_url": req.stream_url,
            "bpm": bpm,
            "duration": duration,
            "difficulty": difficulty,
            "source": req.source,
            "beatmap": beatmap
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clipper/upload")
async def upload_gameplay_recording(video: UploadFile = File(...)):
    """Uploads in-browser canvas recording from MediaRecorder."""
    try:
        raw_name = video.filename or "recording.webm"
        ext = Path(raw_name).suffix.lower()
        if ext not in (".webm", ".mp4", ".mov", ".mkv"):
            ext = ".webm"
        safe_filename = f"rec_{uuid.uuid4().hex[:10]}{ext}"
        target_path = settings.MEDIA_DIR / safe_filename

        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        return {
            "success": True,
            "filename": safe_filename,
            "size_bytes": target_path.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/clipper/render")
async def render_clip_endpoint(req: RenderClipRequest):
    """Renders vertical 9:16 gameplay highlight with HUD overlay using SocialClipperAgent."""
    try:
        clean_video = Path(req.video_filename).name if req.video_filename else ""
        clean_audio = Path(req.audio_filename).name if req.audio_filename else ""
        result = orchestrator.render_clip(
            video_filename=clean_video,
            score=max(0, req.score),
            max_combo=max(0, req.max_combo),
            track_title=req.track_title,
            player_name=req.player_name,
            audio_filename=clean_audio,
        )
        if result.get("status") == "error" or "error" in result:
            err_msg = result.get("message") or result.get("error") or "Failed to render clip"
            raise HTTPException(status_code=400, detail=err_msg)

        # Save clip record to database
        if result.get("clip_id"):
            DatabaseService.save_clip_record(
                clip_id=result["clip_id"],
                filename=result.get("filename", f"{result['clip_id']}.mp4"),
                clip_url=result.get("clip_url", f"/static/media/clips/{result['clip_id']}"),
                player_name=req.player_name,
                track_title=req.track_title,
                score=req.score,
                max_combo=req.max_combo,
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scores/save")
async def save_score_endpoint(req: SaveScoreRequest):
    """Saves player game performance and combo stats to SQLite database."""
    try:
        saved = DatabaseService.save_game_session(
            player_name=req.player_name,
            track_title=req.track_title,
            difficulty=req.difficulty,
            score=req.score,
            max_combo=req.max_combo,
            accuracy=req.accuracy,
            grade=req.grade,
            perfect_hits=req.perfect_hits,
            great_hits=req.great_hits,
            good_hits=req.good_hits,
            misses=req.misses,
        )
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database save error: {str(e)}")


@app.get("/api/scores/leaderboard")
async def get_leaderboard_endpoint(track_title: Optional[str] = None, limit: int = 10):
    """Retrieves top scores globally or filtered by song from database."""
    try:
        data = DatabaseService.get_leaderboard(track_title=track_title, limit=min(50, max(1, limit)))
        return {"leaderboard": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scores/recent")
async def get_recent_scores_endpoint(limit: int = 15):
    """Retrieves recently played game runs from database."""
    try:
        data = DatabaseService.get_recent_sessions(limit=min(50, max(1, limit)))
        return {"recent": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scores/stats")
async def get_stats_endpoint():
    """Retrieves aggregate player statistics and high scores from database."""
    try:
        return DatabaseService.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clips")
async def get_saved_clips_endpoint(limit: int = 20):
    """Retrieves exported highlight video clips saved in database."""
    try:
        clips = DatabaseService.get_saved_clips(limit=min(50, max(1, limit)))
        return {"clips": clips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/chat")
async def agent_chat(req: ChatRequest):
    """Conversational endpoint communicating with FaceBeatOrchestrator and subagents."""
    try:
        response_text = await orchestrator.chat(req.prompt)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health status and agent readiness check."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "agents": [s.name for s in orchestrator.agent_config.subagents],
        "spotify_enabled": SpotifyService.is_configured(),
        "database_connected": settings.DATABASE_PATH.exists(),
    }
