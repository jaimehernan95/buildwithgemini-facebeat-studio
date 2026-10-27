import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_index_endpoint():
    """Verify index route renders HTML template successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "FaceBeat Studio" in response.text
    assert "<video id=\"webcam\"" in response.text


def test_health_endpoint():
    """Verify health endpoint returns status and registered agents."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "RhythmAnalyzerAgent" in data["agents"]
    assert "AudioSafetyAgent" in data["agents"]
    assert "SocialClipperAgent" in data["agents"]


def test_tracks_catalog():
    """Verify track listing returns safe tracks."""
    response = client.get("/api/tracks")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert len(data["tracks"]) >= 3


def test_analyze_endpoint():
    """Verify beat analysis endpoint returns valid beatmap."""
    response = client.post(
        "/api/tracks/analyze",
        json={"filename": "cyber_synth_beat.wav", "difficulty": "normal"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "bpm" in data
    assert "targets" in data
    assert len(data["targets"]) > 0


def test_safety_check_endpoint():
    """Verify safety check endpoint."""
    response = client.post(
        "/api/tracks/safety-check",
        json={"track_title": "Neon Grid Pulse", "artist": "FaceBeat SafeStudio"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_copyright_safe"] is True


def test_agent_chat_endpoint():
    """Verify agent chat endpoint returns a response."""
    response = client.post(
        "/api/agents/chat",
        json={"prompt": "What is the status of FaceBeat-Studio?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
