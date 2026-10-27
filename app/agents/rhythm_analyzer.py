import json
from pathlib import Path
from typing import Dict, Any
from google.antigravity import types
from app.config import settings
from app.services.audio_processor import AudioProcessor


def analyze_audio_track(track_filename: str, difficulty: str = "normal") -> str:
    """Analyzes an audio file in the static audio library (BPM, energy, downbeats)
    and generates a real-time beat map for game targets.

    Args:
        track_filename: The name of the file in app/static/audio (e.g. 'lofi_piano_chill.wav').
        difficulty: The game difficulty ('easy', 'normal', or 'hard').

    Returns:
        A JSON string containing the BPM, total targets, and target timing list.
    """
    file_path = settings.AUDIO_DIR / track_filename
    if not file_path.exists():
        # Check if full path was provided
        p = Path(track_filename)
        if p.exists():
            file_path = p
        else:
            return json.dumps({
                "error": f"Track file not found: {track_filename}",
                "available": [f.name for f in settings.AUDIO_DIR.glob("*.wav")]
            })

    try:
        result = AudioProcessor.analyze_audio(file_path, difficulty=difficulty)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def generate_beatmap_from_tempo(bpm: float, duration_seconds: float = 30.0, difficulty: str = "normal") -> str:
    """Generates a synthetic rhythm beatmap given a BPM tempo and duration (useful for Spotify tracks
    when raw audio files are not locally stored).

    Args:
        bpm: Beats per minute (e.g. 120.0).
        duration_seconds: Duration in seconds.
        difficulty: 'easy', 'normal', or 'hard'.

    Returns:
        JSON string containing the beatmap with targets.
    """
    beat_step = 60.0 / max(bpm, 40.0)
    density = {"easy": 2.0, "normal": 1.0, "hard": 0.5}.get(difficulty.lower(), 1.0)
    interval = beat_step * density

    targets = []
    expressions = ["MouthOpen", "Smile", "BrowRaise"]
    lanes = ["left", "center", "right"]

    current_t = 1.0
    idx = 1
    while current_t < duration_seconds - 1.0:
        targets.append({
            "id": idx,
            "time_sec": round(current_t, 3),
            "time_ms": int(current_t * 1000),
            "expression": expressions[(idx - 1) % len(expressions)],
            "lane": lanes[(idx - 1) % len(lanes)],
            "points": 100,
        })
        current_t += interval
        idx += 1

    return json.dumps({
        "bpm": bpm,
        "duration": duration_seconds,
        "difficulty": difficulty,
        "total_targets": len(targets),
        "targets": targets,
    })


def get_rhythm_analyzer_config() -> types.SubagentConfig:
    """Returns the SubagentConfig for the RhythmAnalyzerAgent."""
    return types.SubagentConfig(
        name="RhythmAnalyzerAgent",
        description="Analyzes audio files or Spotify track metadata (BPM, downbeats, frequency peaks) and generates real-time beat maps for game targets.",
        capabilities=types.SubagentCapabilities(
            agent_behavior=types.AgentBehavior.AUTONOMOUS,
            enabled_tools=[
                types.BuiltinTools.VIEW_FILE,
            ],
        ),
        tools=[
            analyze_audio_track,
            generate_beatmap_from_tempo,
        ],
    )
