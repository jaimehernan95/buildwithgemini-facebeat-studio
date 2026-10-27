from pathlib import Path
import pytest
from app.config import settings
from app.services.audio_processor import AudioProcessor


def test_ensure_audio_library():
    """Verify that default copyright-safe tracks and sound effects are generated."""
    tracks = AudioProcessor.ensure_default_audio_library(settings.AUDIO_DIR)
    assert len(tracks) >= 3

    for track in tracks:
        track_path = settings.AUDIO_DIR / track["filename"]
        assert track_path.exists()
        assert track_path.stat().st_size > 1000


def test_analyze_audio_file():
    """Verify that AudioProcessor analyzes frequencies, BPM, and targets from WAV."""
    sample_track = settings.AUDIO_DIR / "lofi_piano_chill.wav"
    assert sample_track.exists()

    result = AudioProcessor.analyze_audio(sample_track, difficulty="normal")
    assert result["bpm"] > 0
    assert result["duration"] > 0
    assert result["total_targets"] > 0

    # Ensure expressions are valid FaceBeat expressions
    valid_expressions = {"MouthOpen", "Smile", "BrowRaise"}
    for t in result["targets"][:10]:
        assert t["expression"] in valid_expressions
        assert t["time_sec"] >= 0
