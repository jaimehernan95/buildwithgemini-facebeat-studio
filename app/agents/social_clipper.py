import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from google.antigravity import types
from app.config import settings
from app.services.video_renderer import VideoRenderer


def render_gameplay_social_clip(
    video_filename: str,
    score: int = 0,
    max_combo: int = 0,
    track_title: str = "Lo-Fi Sunset",
    player_name: str = "FaceBeat Master",
    audio_filename: str = "",
) -> str:
    """Captures the active camera game session recording, syncs audio, and outputs a vertical
    9:15 video clip optimized for TikTok and Instagram Reels sharing.

    Args:
        video_filename: Source recording filename stored in media directory.
        score: Final game score.
        max_combo: Maximum combo streak achieved.
        track_title: Name of the song.
        player_name: Username or handle for the video watermark.
        audio_filename: Optional background audio track to mix.

    Returns:
        JSON string containing the clip export URL and status.
    """
    input_video = settings.MEDIA_DIR / video_filename
    if not input_video.exists():
        return json.dumps({
            "status": "error",
            "message": f"Recorded video file not found: {video_filename}",
            "expected_dir": str(settings.MEDIA_DIR)
        })

    clip_id = f"clip_{uuid.uuid4().hex[:8]}.mp4"
    output_clip = settings.CLIPS_DIR / clip_id

    audio_path = None
    if audio_filename:
        cand = settings.AUDIO_DIR / audio_filename
        if cand.exists():
            audio_path = cand

    try:
        result = VideoRenderer.render_vertical_clip(
            input_video_path=input_video,
            output_clip_path=output_clip,
            audio_path=audio_path,
            score=score,
            max_combo=max_combo,
            track_title=track_title,
            player_name=player_name,
        )
        if not result.get("success"):
            return json.dumps({"status": "error", "message": result.get("error", "Transcoding failed")})

        return json.dumps({
            "status": "success",
            "clip_id": clip_id,
            "clip_url": result.get("clip_url", f"/static/media/clips/{clip_id}"),
            "aspect_ratio": "9:16",
            "message": "Vertical clip ready for TikTok & Instagram Reels!",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def list_exported_clips() -> str:
    """Lists all previously exported 9:16 social video clips."""
    clips = []
    for f in settings.CLIPS_DIR.glob("*.mp4"):
        clips.append({
            "filename": f.name,
            "url": f"/static/media/clips/{f.name}",
            "size_kb": round(f.stat().st_size / 1024, 1),
        })
    return json.dumps({"clips": clips})


def get_social_clipper_config() -> types.SubagentConfig:
    """Returns the SubagentConfig for the SocialClipperAgent."""
    return types.SubagentConfig(
        name="SocialClipperAgent",
        description="Captures the active camera game session, syncs the audio, and outputs a vertical 9:15 video clip optimized for TikTok and Instagram Reels sharing.",
        capabilities=types.SubagentCapabilities(
            agent_behavior=types.AgentBehavior.AUTONOMOUS,
            enabled_tools=[
                types.BuiltinTools.VIEW_FILE,
            ],
        ),
        tools=[
            render_gameplay_social_clip,
            list_exported_clips,
        ],
    )
