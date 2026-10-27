"""
test_music_services.py - Unit and integration tests for Jamendo & Spotify music services.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.jamendo_service import JamendoService
from app.services.spotify_service import SpotifyService

client = TestClient(app)


def test_jamendo_service_catalog_and_search():
    """Verify JamendoService returns curated and search results with uniform schemas."""
    # Trending / empty query
    trending = JamendoService.get_trending_tracks(limit=5)
    assert len(trending) > 0
    first = trending[0]
    assert "id" in first
    assert "title" in first
    assert "artist" in first
    assert "bpm" in first
    assert "stream_url" in first
    assert "cover_art" in first
    assert first["source"] == "jamendo"

    # Specific keyword search
    results = JamendoService.search_tracks(query="cyber", limit=3)
    assert len(results) > 0
    assert any("cyber" in r["title"].lower() or "cyber" in r["genre"].lower() for r in results)


def test_spotify_service_catalog_and_search():
    """Verify SpotifyService returns curated hits with valid metadata and artwork."""
    # Empty query returns curated hits
    hits = SpotifyService.search_tracks(query="", limit=4)
    assert len(hits) == 4
    first = hits[0]
    assert "id" in first
    assert "title" in first
    assert "artist" in first
    assert "cover_art" in first
    assert "bpm" in first
    assert first["source"] == "spotify"

    # Search for specific artist
    results = SpotifyService.search_tracks(query="weeknd", limit=2)
    assert len(results) > 0
    assert any("weeknd" in r["artist"].lower() for r in results)


def test_jamendo_api_endpoints():
    """Test Jamendo REST API routes."""
    # Trending route
    resp = client.get("/api/music/jamendo/trending?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert "tracks" in data
    assert len(data["tracks"]) <= 3

    # Search route
    resp = client.get("/api/music/jamendo/search?q=sunset&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "sunset"
    assert len(data["tracks"]) > 0


def test_spotify_api_endpoints():
    """Test Spotify REST API routes."""
    resp = client.get("/api/music/spotify/search?q=dua&limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "dua"
    assert len(data["tracks"]) > 0
    assert "configured" in data


def test_music_select_beatmap_generation():
    """Test POST /api/music/select generates beatmaps for online tracks."""
    payload = {
        "track_id": "jam_101",
        "title": "Cyber Sunset Drive",
        "artist": "Neon Runner",
        "stream_url": "/static/audio/cyber_synth_beat.wav",
        "bpm": 128.0,
        "duration": 60.0,
        "difficulty": "normal",
        "source": "jamendo"
    }
    resp = client.post("/api/music/select", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["bpm"] == 128.0
    assert "beatmap" in data
    assert "targets" in data["beatmap"]
    assert len(data["beatmap"]["targets"]) > 20
    # Targets should have valid expressions
    for t in data["beatmap"]["targets"][:5]:
        assert t["expression"] in ("MouthOpen", "Smile", "BrowRaise")
