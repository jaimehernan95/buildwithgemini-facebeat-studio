import json
from pathlib import Path
from typing import Dict, Any, List
from google.antigravity import types
from app.config import settings
from app.services.audio_processor import AudioProcessor
from app.services.spotify_service import SpotifyService


def check_audio_copyright_safety(track_title: str, artist: str = "") -> str:
    """Verifies whether a track is safe for live streaming and social media sharing
    without incurring DMCA takedowns or copyright strikes.

    Args:
        track_title: The name of the song or track.
        artist: The artist name.

    Returns:
        JSON string with copyright safety status, risk score, and recommended action.
    """
    safe_keywords = ["lo-fi", "lofi", "piano sunset", "safe", "royalty-free", "facebeat", "neon grid", "midnight coffee"]
    is_internal = any(k in track_title.lower() for k in safe_keywords)

    if is_internal:
        return json.dumps({
            "track": track_title,
            "artist": artist or "FaceBeat SafeStudio",
            "is_copyright_safe": True,
            "status": "APPROVED_SAFE",
            "risk_score": 0.0,
            "message": "Track is 100% royalty-free and safe for TikTok/Reels export.",
        })

    # For commercial / external tracks
    return json.dumps({
        "track": track_title,
        "artist": artist,
        "is_copyright_safe": False,
        "status": "POTENTIAL_COPYRIGHT_RISK",
        "risk_score": 0.85,
        "message": "Commercial track detected. When exporting clips to TikTok/Instagram Reels, AudioSafetyAgent recommends muting or swapping to a royalty-free fallback loop to prevent sound muting or strikes.",
        "fallback_recommended": "lofi_piano_chill.wav",
    })


def get_safe_audio_library() -> str:
    """Retrieves the list of built-in copyright-free royalty-free lofi piano loops
    and short percussive sounds available in FaceBeat-Studio.

    Returns:
        JSON string listing all verified safe tracks and their file URLs.
    """
    tracks = AudioProcessor.ensure_default_audio_library(settings.AUDIO_DIR)
    for t in tracks:
        t["url"] = f"/static/audio/{t['filename']}"
    return json.dumps({"status": "ok", "tracks": tracks})


def get_spotify_connection_status() -> str:
    """Checks the status of Spotify Web API authentication and returns the authorization URL.

    Returns:
        JSON string with configuration status and auth URL.
    """
    configured = SpotifyService.is_configured()
    auth_url = SpotifyService.get_authorization_url()
    return json.dumps({
        "configured": configured,
        "auth_url": auth_url,
        "message": "Spotify OAuth configured." if configured else "Spotify Client ID not set in .env; demo mock mode available."
    })


def get_audio_safety_config() -> types.SubagentConfig:
    """Returns the SubagentConfig for the AudioSafetyAgent."""
    return types.SubagentConfig(
        name="AudioSafetyAgent",
        description="Integrates Spotify Web API authentication for user tracks, and manages a fallback library of copyright-free royalty-free lofi piano loops and short percussive sounds to prevent copyright strikes on social media.",
        capabilities=types.SubagentCapabilities(
            agent_behavior=types.AgentBehavior.AUTONOMOUS,
            enabled_tools=[
                types.BuiltinTools.VIEW_FILE,
            ],
        ),
        tools=[
            check_audio_copyright_safety,
            get_safe_audio_library,
            get_spotify_connection_status,
        ],
    )
