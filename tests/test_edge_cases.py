import pytest
import tempfile
import wave
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.audio_processor import AudioProcessor
from app.services.video_renderer import VideoRenderer
from app.config import settings

client = TestClient(app)


def test_audio_edge_case_missing_file():
    """Verify that analyzing a nonexistent audio file returns a safe fallback beatmap."""
    res = AudioProcessor.analyze_audio(Path("/nonexistent/file.wav"), difficulty="normal")
    assert res["bpm"] > 0
    assert res["total_targets"] > 0
    assert len(res["targets"]) > 0


def test_audio_edge_case_invalid_difficulty():
    """Verify that passing an unknown or malformed difficulty normalizes safely."""
    path = settings.AUDIO_DIR / "lofi_piano_chill.wav"
    res = AudioProcessor.analyze_audio(path, difficulty="ultra_extreme_nightmare")
    assert res["difficulty"] == "normal"
    assert res["bpm"] > 0


def test_audio_edge_case_sub_second_audio():
    """Verify that sub-second audio files do not cause ZeroDivisionError or index faults."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        temp_path = Path(tf.name)

    sr = 44100
    short_samples = (np.sin(2 * np.pi * 440 * np.linspace(0, 0.25, int(sr * 0.25))) * 32767).astype(np.int16)
    with wave.open(str(temp_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(short_samples.tobytes())

    res = AudioProcessor.analyze_audio(temp_path)
    temp_path.unlink(missing_ok=True)

    assert res["bpm"] > 0
    assert res["total_targets"] > 0


def test_video_drawtext_sanitization():
    """Verify that FFmpeg drawtext filter sanitizes colons, quotes, percent signs, and backslashes."""
    dirty_text = "Track: 100% 'Funky': Test & [Synth]\\Escape"
    clean = VideoRenderer._sanitize_drawtext(dirty_text)
    assert "'" not in clean
    assert "%" not in clean
    assert "\\:" in clean  # Colons properly escaped for FFmpeg


def test_video_edge_case_missing_source():
    """Verify that attempting to render a missing video file returns a clean error dict."""
    res = VideoRenderer.render_vertical_clip(
        input_video_path=Path("/tmp/nonexistent_video.webm"),
        output_clip_path=Path("/tmp/clip_out.mp4"),
        score=0,
        max_combo=0,
    )
    assert res["success"] is False
    assert "error" in res


def test_api_edge_case_path_traversal():
    """Verify that path traversal strings in audio analysis requests are neutralized."""
    response = client.post("/api/tracks/analyze", json={"filename": "../../../../../etc/passwd", "difficulty": "normal"})
    # Should either succeed with fallback beatmap or 404, never 500
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "bpm" in data


def test_api_edge_case_clipper_bad_inputs():
    """Verify that negative scores, combos, and missing video files return 400 or 404 without 500."""
    response = client.post(
        "/api/clipper/render",
        json={
            "video_filename": "../../secret.mp4",
            "score": -999,
            "max_combo": -10,
            "track_title": "Bad Input",
            "player_name": "Edge Player",
        },
    )
    assert response.status_code in (400, 404)
    assert response.status_code != 500


def test_api_edge_case_whitespace_safety_check():
    """Verify that whitespace-only track title in safety check does not crash."""
    response = client.post("/api/tracks/safety-check", json={"track_title": "   "})
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
