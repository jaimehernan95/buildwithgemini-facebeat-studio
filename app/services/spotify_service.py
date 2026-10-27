"""
spotify_service.py - Spotify Web API integration for FaceBeat-Studio.
Provides:
- OAuth authorization & user playback access token flow
- Client credentials flow for public track search & metadata
- Audio Features analysis (BPM, danceability, energy)
- Curated pop catalog fallback for zero-configuration testing
"""

import urllib.parse
import logging
from typing import Dict, List, Any, Optional
import requests
from app.config import settings

logger = logging.getLogger(__name__)


class SpotifyService:
    """Spotify Web API integration for track authentication, search, and analysis."""

    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"

    # Curated Spotify Pop & Dance catalog with artwork, BPM, and audio fallbacks
    CURATED_SPOTIFY_HITS: List[Dict[str, Any]] = [
        {
            "id": "sp_blinding_lights",
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
            "bpm": 171,
            "duration": 60,
            "stream_url": "/static/audio/cyber_synth_beat.wav",
            "cover_art": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80",
            "source": "spotify",
            "preview_url": "/static/audio/cyber_synth_beat.wav",
            "spotify_url": "https://open.spotify.com/track/0VjIjW4GlULA75m25iJ70M"
        },
        {
            "id": "sp_levitating",
            "title": "Levitating",
            "artist": "Dua Lipa",
            "album": "Future Nostalgia",
            "bpm": 103,
            "duration": 60,
            "stream_url": "/static/audio/funk_acoustic_groove.wav",
            "cover_art": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&q=80",
            "source": "spotify",
            "preview_url": "/static/audio/funk_acoustic_groove.wav",
            "spotify_url": "https://open.spotify.com/track/463CkQjx2Zk1yXoBuierM9"
        },
        {
            "id": "sp_one_more_time",
            "title": "One More Time",
            "artist": "Daft Punk",
            "album": "Discovery",
            "bpm": 123,
            "duration": 60,
            "stream_url": "/static/audio/cyber_synth_beat.wav",
            "cover_art": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=300&q=80",
            "source": "spotify",
            "preview_url": "/static/audio/cyber_synth_beat.wav",
            "spotify_url": "https://open.spotify.com/track/0DiWol3AO6WpXZgp0gGlNW"
        },
        {
            "id": "sp_24k_magic",
            "title": "24K Magic",
            "artist": "Bruno Mars",
            "album": "24K Magic",
            "bpm": 106,
            "duration": 60,
            "stream_url": "/static/audio/funk_acoustic_groove.wav",
            "cover_art": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&q=80",
            "source": "spotify",
            "preview_url": "/static/audio/funk_acoustic_groove.wav",
            "spotify_url": "https://open.spotify.com/track/6b8Be6ljOzmk1zslV1eXt8"
        },
        {
            "id": "sp_bad_guy",
            "title": "bad guy",
            "artist": "Billie Eilish",
            "album": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?",
            "bpm": 135,
            "duration": 60,
            "stream_url": "/static/audio/cyber_synth_beat.wav",
            "cover_art": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300&q=80",
            "source": "spotify",
            "preview_url": "/static/audio/cyber_synth_beat.wav",
            "spotify_url": "https://open.spotify.com/track/2Fxmhks0bxGSBdJ92v4422"
        },
        {
            "id": "sp_sunflower",
            "title": "Sunflower",
            "artist": "Post Malone & Swae Lee",
            "album": "Spider-Man: Into the Spider-Verse",
            "bpm": 90,
            "duration": 60,
            "stream_url": "/static/audio/lofi_piano_chill.wav",
            "cover_art": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300&q=80",
            "source": "spotify",
            "preview_url": "/static/audio/lofi_piano_chill.wav",
            "spotify_url": "https://open.spotify.com/track/3KkXRQHbMCARz0aVfEt68P"
        }
    ]

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if Spotify client credentials are configured."""
        return bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET)

    @classmethod
    def get_authorization_url(cls, state: str = "facebeat_state") -> str:
        """Builds the Spotify OAuth 2.0 authorization URL."""
        if not cls.is_configured():
            return f"/api/spotify/callback?mock=true&state={state}"

        params = {
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "scope": "user-read-playback-state user-modify-playback-state streaming user-read-currently-playing",
            "state": state,
            "show_dialog": "true",
        }
        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def exchange_code_for_token(cls, code: str) -> Dict[str, Any]:
        """Exchanges an authorization code for an access token."""
        if not cls.is_configured():
            return {
                "access_token": "mock_spotify_token_facebeat_demo",
                "token_type": "Bearer",
                "expires_in": 3600,
                "is_mock": True,
            }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(cls.TOKEN_URL, data=data, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": response.text, "status_code": response.status_code}

    @classmethod
    def get_client_credentials_token(cls) -> Optional[str]:
        """Fetches an application-level token for public searching."""
        if not cls.is_configured():
            return None

        try:
            data = {"grant_type": "client_credentials"}
            auth = (settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET)
            resp = requests.post(cls.TOKEN_URL, data=data, auth=auth, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("access_token")
        except Exception as e:
            logger.warning(f"Error fetching Spotify client credentials token: {e}")
        return None

    @classmethod
    def search_tracks(cls, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Searches Spotify for matching tracks with album covers, artist names, and BPM.
        Falls back to curated hits when unconfigured or rate-limited.
        """
        clean_query = (query or "").strip().lower()

        token = cls.get_client_credentials_token()
        if token and clean_query:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                params = {"q": clean_query, "type": "track", "limit": min(20, max(1, limit))}
                resp = requests.get(f"{cls.API_BASE}/search", headers=headers, params=params, timeout=5)
                if resp.status_code == 200:
                    items = resp.json().get("tracks", {}).get("items", [])
                    if items:
                        formatted = []
                        for it in items:
                            images = it.get("album", {}).get("images", [])
                            cover = images[0]["url"] if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80"
                            artists = ", ".join([a["name"] for a in it.get("artists", [])]) or "Unknown Artist"
                            preview = it.get("preview_url") or "/static/audio/cyber_synth_beat.wav"

                            formatted.append({
                                "id": f"sp_{it.get('id')}",
                                "title": it.get("name", "Unknown Title"),
                                "artist": artists,
                                "album": it.get("album", {}).get("name", "Unknown Album"),
                                "bpm": 120,
                                "duration": int(it.get("duration_ms", 60000) / 1000),
                                "stream_url": preview,
                                "cover_art": cover,
                                "source": "spotify",
                                "preview_url": preview,
                                "spotify_url": it.get("external_urls", {}).get("spotify", "")
                            })
                        return formatted[:limit]
            except Exception as e:
                logger.warning(f"Error querying Spotify search API: {e}")

        # Curated catalog search
        if not clean_query:
            return cls.CURATED_SPOTIFY_HITS[:limit]

        matches = [
            t for t in cls.CURATED_SPOTIFY_HITS
            if clean_query in t["title"].lower()
            or clean_query in t["artist"].lower()
            or clean_query in t["album"].lower()
        ]

        if not matches:
            return cls.CURATED_SPOTIFY_HITS[:limit]

        return matches[:limit]

    @classmethod
    def get_track_audio_features(cls, track_id: str, access_token: str) -> Dict[str, Any]:
        """Retrieves tempo, time signature, and energy from Spotify Audio Features API."""
        if not access_token or access_token.startswith("mock_"):
            return {
                "track_id": track_id,
                "tempo": 124.0,
                "time_signature": 4,
                "danceability": 0.78,
                "energy": 0.82,
                "duration_ms": 180000,
                "is_mock": True,
            }

        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{cls.API_BASE}/audio-features/{track_id}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": response.text, "status_code": response.status_code}
