import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import settings


class VideoRenderer:
    """Renders gameplay video clips into vertical 9:16 format optimized for TikTok and Instagram Reels."""

    FFMPEG_BIN = "/usr/bin/ffmpeg"

    @staticmethod
    def _sanitize_drawtext(text: str, default: str = "FaceBeat") -> str:
        """Sanitizes strings for safe inclusion in FFmpeg drawtext filter graph."""
        if not text:
            return default
        # Remove control characters, quotes, percent signs, and backslashes
        cleaned = re.sub(r'[\r\n\t\'"\\%]', '', str(text).strip())
        # Escape colons for ffmpeg filter syntax
        escaped = cleaned.replace(":", "\\:")
        # Truncate length for layout sanity
        return escaped[:45] if escaped else default

    @classmethod
    def render_vertical_clip(
        cls,
        input_video_path: Path,
        output_clip_path: Path,
        audio_path: Optional[Path] = None,
        score: int = 0,
        max_combo: int = 0,
        track_title: str = "FaceBeat Jam",
        player_name: str = "Player",
    ) -> Dict[str, Any]:
        """
        Transcodes and crops/pads input video to 9:16 vertical ratio (720x1280),
        burns in game HUD stats (Score, Combo, Player), and muxes audio.
        Handles edge cases such as missing/empty files, extreme scores, and special characters.
        """
        if not input_video_path.exists() or input_video_path.stat().st_size == 0:
            return {
                "success": False,
                "error": f"Source video missing or empty: {input_video_path}",
                "clip_path": None,
                "clip_url": None,
            }

        output_clip_path.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize text overlays for ffmpeg drawtext filter
        safe_title = cls._sanitize_drawtext(track_title, default="FaceBeat Jam")
        safe_player = cls._sanitize_drawtext(player_name, default="Player")
        safe_score = max(0, int(score))
        safe_combo = max(0, int(max_combo))

        # 9:16 aspect ratio scaling & padding (720x1280)
        filter_complex = (
            "[0:v]scale=720:1280:force_original_aspect_ratio=decrease,"
            "pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=#110b29,"
            "drawtext=text='FACEBEAT STUDIO':fontsize=32:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8:x=(w-text_w)/2:y=60,"
            f"drawtext=text='Track\\: {safe_title}':fontsize=22:fontcolor=0x00FFCC:box=1:boxcolor=black@0.5:boxborderw=6:x=(w-text_w)/2:y=120,"
            f"drawtext=text='SCORE\\: {safe_score}  |  MAX COMBO\\: {safe_combo}x':fontsize=26:fontcolor=0xFF007F:box=1:boxcolor=black@0.7:boxborderw=8:x=(w-text_w)/2:y=h-140,"
            f"drawtext=text='{safe_player}':fontsize=20:fontcolor=white:x=(w-text_w)/2:y=h-80[v]"
        )

        cmd = [
            cls.FFMPEG_BIN,
            "-y",
            "-i", str(input_video_path),
        ]

        if audio_path and audio_path.exists() and audio_path.stat().st_size > 0:
            cmd.extend(["-i", str(audio_path)])
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "1:a:0",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
            ])
        else:
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-c:a", "aac",
            ])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_clip_path),
        ])

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return {
                "success": True,
                "clip_path": str(output_clip_path),
                "clip_url": f"/static/media/clips/{output_clip_path.name}",
                "aspect_ratio": "9:16",
                "resolution": "720x1280",
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"FFmpeg transcoding failed: {e.stderr[:300] if e.stderr else str(e)}",
                "clip_path": None,
                "clip_url": None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected rendering error: {str(e)}",
                "clip_path": None,
                "clip_url": None,
            }

    @classmethod
    def list_clips(cls) -> list[Dict[str, Any]]:
        """Lists all previously exported social clips in chronological order."""
        clips = []
        if settings.CLIPS_DIR.exists():
            for p in sorted(settings.CLIPS_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True):
                clips.append({
                    "filename": p.name,
                    "url": f"/static/media/clips/{p.name}",
                    "size_bytes": p.stat().st_size,
                    "created_at": p.stat().st_mtime,
                })
        return clips
