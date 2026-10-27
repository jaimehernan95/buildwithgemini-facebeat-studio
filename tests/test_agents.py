import json
import pytest
from app.agents.orchestrator import FaceBeatOrchestrator
from app.agents.rhythm_analyzer import get_rhythm_analyzer_config, generate_beatmap_from_tempo
from app.agents.audio_safety import get_audio_safety_config, check_audio_copyright_safety
from app.agents.social_clipper import get_social_clipper_config


def test_agent_configurations():
    """Verify that all three Antigravity subagents are configured properly."""
    rhythm = get_rhythm_analyzer_config()
    safety = get_audio_safety_config()
    clipper = get_social_clipper_config()

    assert rhythm.name == "RhythmAnalyzerAgent"
    assert safety.name == "AudioSafetyAgent"
    assert clipper.name == "SocialClipperAgent"

    assert len(rhythm.tools) >= 2
    assert len(safety.tools) >= 2
    assert len(clipper.tools) >= 2


def test_orchestrator_initialization():
    """Verify that the orchestrator registers all subagents in LocalAgentConfig."""
    orchestrator = FaceBeatOrchestrator()
    subagent_names = [s.name for s in orchestrator.agent_config.subagents]

    assert "RhythmAnalyzerAgent" in subagent_names
    assert "AudioSafetyAgent" in subagent_names
    assert "SocialClipperAgent" in subagent_names
    assert orchestrator.agent_config.capabilities.enable_subagents is True


def test_rhythm_beatmap_generation():
    """Test generating a synthetic beatmap from tempo."""
    raw = generate_beatmap_from_tempo(bpm=120.0, duration_seconds=10.0, difficulty="normal")
    data = json.loads(raw)

    assert data["bpm"] == 120.0
    assert data["total_targets"] > 0
    first_target = data["targets"][0]
    assert "time_sec" in first_target
    assert "expression" in first_target
    assert first_target["expression"] in ["MouthOpen", "Smile", "BrowRaise"]


def test_audio_safety_checks():
    """Test copyright verification for royalty-free vs commercial tracks."""
    safe_res = json.loads(check_audio_copyright_safety("Lo-Fi Piano Sunset"))
    assert safe_res["is_copyright_safe"] is True
    assert safe_res["status"] == "APPROVED_SAFE"

    commercial_res = json.loads(check_audio_copyright_safety("Blinding Lights", "The Weeknd"))
    assert commercial_res["is_copyright_safe"] is False
    assert commercial_res["status"] == "POTENTIAL_COPYRIGHT_RISK"
