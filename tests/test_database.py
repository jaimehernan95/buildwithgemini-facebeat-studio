import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.database import DatabaseService

client = TestClient(app)


def test_database_initialization():
    """Verify SQLite database schema tables are created successfully."""
    conn = DatabaseService.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "game_sessions" in tables
    assert "player_profiles" in tables
    assert "exported_clips" in tables


def test_database_save_and_retrieve_session():
    """Verify saving a game session persists record and updates player profile."""
    res = DatabaseService.save_game_session(
        player_name="TestCyberHero",
        track_title="Lo-Fi Piano Sunset",
        difficulty="hard",
        score=95400,
        max_combo=84,
        accuracy=98.5,
        grade="S",
        perfect_hits=75,
        great_hits=9,
        good_hits=0,
        misses=1,
    )

    assert res["saved"] is True
    assert res["session_id"] > 0
    assert res["score"] == 95400
    assert res["grade"] == "S"

    # Check player profile updated
    profile = DatabaseService.get_player_profile("TestCyberHero")
    assert profile is not None
    assert profile["high_score"] >= 95400
    assert profile["total_plays"] >= 1


def test_database_leaderboard_ordering():
    """Verify leaderboard returns records sorted by score descending."""
    DatabaseService.save_game_session(
        player_name="PlayerLow",
        track_title="Neon Grid Pulse",
        difficulty="normal",
        score=10000,
        max_combo=10,
    )
    DatabaseService.save_game_session(
        player_name="PlayerHigh",
        track_title="Neon Grid Pulse",
        difficulty="normal",
        score=88888,
        max_combo=55,
    )

    leaderboard = DatabaseService.get_leaderboard(track_title="Neon Grid Pulse", limit=10)
    assert len(leaderboard) >= 2
    # Verify descending score order
    scores = [r["score"] for r in leaderboard]
    assert scores == sorted(scores, reverse=True)


def test_database_stats():
    """Verify aggregate statistics calculation."""
    stats = DatabaseService.get_stats()
    assert stats["total_games"] > 0
    assert stats["all_time_high_score"] > 0
    assert stats["max_combo_record"] > 0
    assert stats["average_score"] > 0


def test_database_clip_persistence():
    """Verify saving and retrieving exported video clips."""
    clip_id = "test_clip_persistence_123"
    DatabaseService.save_clip_record(
        clip_id=clip_id,
        filename=f"{clip_id}.mp4",
        clip_url=f"/static/media/clips/{clip_id}.mp4",
        player_name="ClipStar",
        track_title="Midnight Coffee Funk",
        score=72000,
        max_combo=45,
    )

    clips = DatabaseService.get_saved_clips(limit=10)
    match = next((c for c in clips if c["clip_id"] == clip_id), None)
    assert match is not None
    assert match["player_name"] == "ClipStar"
    assert match["score"] == 72000


def test_api_save_score_endpoint():
    """Verify POST /api/scores/save endpoint."""
    payload = {
        "player_name": "APIPlayer",
        "track_title": "Lo-Fi Piano Sunset",
        "difficulty": "normal",
        "score": 54200,
        "max_combo": 38,
        "accuracy": 92.4,
        "grade": "A",
        "perfect_hits": 30,
        "great_hits": 8,
        "good_hits": 2,
        "misses": 3,
    }
    resp = client.post("/api/scores/save", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["saved"] is True
    assert data["player_name"] == "APIPlayer"
    assert data["score"] == 54200


def test_api_leaderboard_and_stats_endpoints():
    """Verify GET /api/scores/leaderboard and GET /api/scores/stats endpoints."""
    lb_resp = client.get("/api/scores/leaderboard?limit=5")
    assert lb_resp.status_code == 200
    lb_data = lb_resp.json()
    assert "leaderboard" in lb_data
    assert isinstance(lb_data["leaderboard"], list)

    stats_resp = client.get("/api/scores/stats")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert "total_games" in stats_data
    assert "all_time_high_score" in stats_data

    clips_resp = client.get("/api/clips?limit=5")
    assert clips_resp.status_code == 200
    assert "clips" in clips_resp.json()
