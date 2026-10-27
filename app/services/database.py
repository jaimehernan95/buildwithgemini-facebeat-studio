"""
database.py - SQLite Database Storage Manager for FaceBeat-Studio.
Manages persistent game session history, high scores leaderboard,
player statistics, and exported social clips.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.config import settings


class DatabaseService:
    """Manages SQLite storage and retrieval for FaceBeat-Studio."""

    _db_path: Path = settings.DATABASE_PATH

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Opens a connection to the SQLite database with row factory enabled."""
        settings.ensure_directories()
        conn = sqlite3.connect(cls._db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high performance concurrent reads and writes
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    @classmethod
    def init_db(cls) -> None:
        """Initializes database schema and indexes."""
        with cls.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    track_title TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    max_combo INTEGER NOT NULL,
                    accuracy REAL DEFAULT 100.0,
                    grade TEXT DEFAULT 'A',
                    perfect_hits INTEGER DEFAULT 0,
                    great_hits INTEGER DEFAULT 0,
                    good_hits INTEGER DEFAULT 0,
                    misses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS exported_clips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clip_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    clip_url TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    track_title TEXT NOT NULL,
                    score INTEGER DEFAULT 0,
                    max_combo INTEGER DEFAULT 0,
                    aspect_ratio TEXT DEFAULT '9:16',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS player_profiles (
                    player_name TEXT PRIMARY KEY,
                    total_games INTEGER DEFAULT 0,
                    high_score INTEGER DEFAULT 0,
                    total_score INTEGER DEFAULT 0,
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_score ON game_sessions(score DESC);
                CREATE INDEX IF NOT EXISTS idx_sessions_track ON game_sessions(track_title);
                CREATE INDEX IF NOT EXISTS idx_clips_created ON exported_clips(created_at DESC);
            """)

    @classmethod
    def save_game_session(
        cls,
        player_name: str,
        track_title: str,
        difficulty: str,
        score: int,
        max_combo: int,
        accuracy: float = 100.0,
        grade: str = "A",
        perfect_hits: int = 0,
        great_hits: int = 0,
        good_hits: int = 0,
        misses: int = 0,
    ) -> Dict[str, Any]:
        """Saves a completed game run and updates player profile stats."""
        cls.init_db()
        player = (player_name or "Cyber Dancer").strip() or "Cyber Dancer"
        track = (track_title or "Lo-Fi Piano Sunset").strip() or "Lo-Fi Piano Sunset"
        diff = (difficulty or "normal").lower()

        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO game_sessions (
                    player_name, track_title, difficulty, score, max_combo,
                    accuracy, grade, perfect_hits, great_hits, good_hits, misses, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    player,
                    track,
                    diff,
                    score,
                    max_combo,
                    round(accuracy, 1),
                    grade,
                    perfect_hits,
                    great_hits,
                    good_hits,
                    misses,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            session_id = cursor.lastrowid

            # Update or create player profile
            cursor.execute(
                """
                INSERT INTO player_profiles (player_name, total_games, high_score, total_score, last_played)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(player_name) DO UPDATE SET
                    total_games = total_games + 1,
                    high_score = MAX(high_score, excluded.high_score),
                    total_score = total_score + excluded.total_score,
                    last_played = excluded.last_played
                """,
                (player, score, score, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

        return {
            "session_id": session_id,
            "player_name": player,
            "score": score,
            "grade": grade,
            "saved": True,
        }

    @classmethod
    def get_leaderboard(cls, track_title: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves top scores globally or filtered by song."""
        cls.init_db()
        with cls.get_connection() as conn:
            if track_title:
                rows = conn.execute(
                    """
                    SELECT id, player_name, track_title, difficulty, score, max_combo, accuracy, grade, created_at
                    FROM game_sessions
                    WHERE track_title = ?
                    ORDER BY score DESC, created_at DESC
                    LIMIT ?
                    """,
                    (track_title, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, player_name, track_title, difficulty, score, max_combo, accuracy, grade, created_at
                    FROM game_sessions
                    ORDER BY score DESC, created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [dict(r) for r in rows]

    @classmethod
    def get_recent_sessions(cls, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves recently played game sessions."""
        cls.init_db()
        with cls.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, player_name, track_title, difficulty, score, max_combo, accuracy, grade, created_at
                FROM game_sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Calculates global gameplay statistics."""
        cls.init_db()
        with cls.get_connection() as conn:
            summary = conn.execute(
                """
                SELECT
                    COUNT(*) as total_games,
                    COALESCE(MAX(score), 0) as all_time_high_score,
                    COALESCE(ROUND(AVG(score), 0), 0) as avg_score,
                    COALESCE(MAX(max_combo), 0) as max_combo_record
                FROM game_sessions
                """
            ).fetchone()

            top_player = conn.execute(
                """
                SELECT player_name, high_score, total_games
                FROM player_profiles
                ORDER BY high_score DESC
                LIMIT 1
                """
            ).fetchone()

        return {
            "total_games": summary["total_games"],
            "all_time_high_score": summary["all_time_high_score"],
            "avg_score": int(summary["avg_score"]),
            "average_score": int(summary["avg_score"]),
            "max_combo_record": summary["max_combo_record"],
            "top_player": dict(top_player) if top_player else None,
        }

    @classmethod
    def get_player_profile(cls, player_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a player's aggregated profile by handle."""
        cls.init_db()
        with cls.get_connection() as conn:
            row = conn.execute(
                """
                SELECT player_name, total_games, total_games AS total_plays, high_score, total_score, last_played
                FROM player_profiles
                WHERE player_name = ?
                """,
                (player_name.strip(),),
            ).fetchone()
        return dict(row) if row else None

    @classmethod
    def save_clip_record(
        cls,
        clip_id: str,
        filename: str,
        clip_url: str,
        player_name: str,
        track_title: str,
        score: int = 0,
        max_combo: int = 0,
    ) -> Dict[str, Any]:
        """Saves metadata for an exported vertical highlight clip."""
        cls.init_db()
        with cls.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO exported_clips (
                    clip_id, filename, clip_url, player_name, track_title, score, max_combo, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clip_id,
                    filename,
                    clip_url,
                    player_name,
                    track_title,
                    score,
                    max_combo,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return {"clip_id": clip_id, "saved": True}

    @classmethod
    def get_saved_clips(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns saved clips from the database."""
        cls.init_db()
        with cls.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT clip_id, filename, clip_url, player_name, track_title, score, max_combo, created_at
                FROM exported_clips
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


# Initialize DB on module import
DatabaseService.init_db()
