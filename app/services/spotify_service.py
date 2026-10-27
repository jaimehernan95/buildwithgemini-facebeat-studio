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

    # Curated Spotify Pop & Dance catalog with artwork, BPM, and real CDN audio streams
    CURATED_SPOTIFY_HITS: List[Dict[str, Any]] = [
        {
            "id": "sp_starboy",
            "title": "Starboy (feat. Daft Punk)",
            "artist": "The Weeknd",
            "album": "Starboy",
            "bpm": 186,
            "duration": 30,
            "stream_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/11/71/d6/1171d6ad-3c96-e027-2af6-58028426588c/mzaf_15137631797407745471.plus.aac.p.m4a",
            "cover_art": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80",
            "source": "spotify",
            "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/11/71/d6/1171d6ad-3c96-e027-2af6-58028426588c/mzaf_15137631797407745471.plus.aac.p.m4a",
            "spotify_url": "https://open.spotify.com/track/7MXVkk9YM5IZxh0WSlVIkY"
        },
        {
            "id": "sp_levitating",
            "title": "Levitating",
            "artist": "Dua Lipa",
            "album": "Future Nostalgia",
            "bpm": 103,
            "duration": 30,
            "stream_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/59/dc/4d/59dc4dda-93ff-8f1c-c536-f005f6ea6af5/mzaf_3066686759813252385.plus.aac.p.m4a",
            "cover_art": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&q=80",
            "source": "spotify",
            "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/59/dc/4d/59dc4dda-93ff-8f1c-c536-f005f6ea6af5/mzaf_3066686759813252385.plus.aac.p.m4a",
            "spotify_url": "https://open.spotify.com/track/463CkQjx2Zk1yXoBuierM9"
        },
        {
            "id": "sp_one_more_time",
            "title": "One More Time",
            "artist": "Daft Punk",
            "album": "Discovery",
            "bpm": 123,
            "duration": 30,
            "stream_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/5d/93/d8/5d93d83f-ad1e-da4d-1d79-9937bdff24ec/mzaf_14396932211949300852.plus.aac.p.m4a",
            "cover_art": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=300&q=80",
            "source": "spotify",
            "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/5d/93/d8/5d93d83f-ad1e-da4d-1d79-9937bdff24ec/mzaf_14396932211949300852.plus.aac.p.m4a",
            "spotify_url": "https://open.spotify.com/track/0DiWol3AO6WpXZgp0gGlNW"
        },
        {
            "id": "sp_24k_magic",
            "title": "24K Magic",
            "artist": "Bruno Mars",
            "album": "24K Magic",
            "bpm": 106,
            "duration": 30,
            "stream_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/45/c4/cb/45c4cb28-670f-f1fe-9678-7fa1601bbb5a/mzaf_2006385778979520718.plus.aac.p.m4a",
            "cover_art": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&q=80",
            "source": "spotify",
            "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/45/c4/cb/45c4cb28-670f-f1fe-9678-7fa1601bbb5a/mzaf_2006385778979520718.plus.aac.p.m4a",
            "spotify_url": "https://open.spotify.com/track/6b8Be6ljOzmk1zslV1eXt8"
        },
        {
            "id": "sp_bad_guy",
            "title": "bad guy",
            "artist": "Billie Eilish",
            "album": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?",
            "bpm": 135,
            "duration": 30,
            "stream_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/c3/87/1f/c3871f7e-3260-d615-1c66-5fdca2c3a48f/mzaf_10721331211699880949.plus.aac.p.m4a",
            "cover_art": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300&q=80",
            "source": "spotify",
            "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/c3/87/1f/c3871f7e-3260-d615-1c66-5fdca2c3a48f/mzaf_10721331211699880949.plus.aac.p.m4a",
            "spotify_url": "https://open.spotify.com/track/2Fxmhks0bxGSBdJ92v4422"
        },
        {
            "id": "sp_sunflower",
            "title": "Sunflower",
            "artist": "Post Malone & Swae Lee",
            "album": "Spider-Man: Into the Spider-Verse",
            "bpm": 90,
            "duration": 30,
            "stream_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/98/f0/d6/98f0d67e-f8bf-762d-cac7-1c6b3b6b35dd/mzaf_4543283896248560946.plus.aac.p.m4a",
            "cover_art": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300&q=80",
            "source": "spotify",
            "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/98/f0/d6/98f0d67e-f8bf-762d-cac7-1c6b3b6b35dd/mzaf_4543283896248560946.plus.aac.p.m4a",
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
    def search_public_music_catalog(cls, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Queries universal open music database with zero API keys required.
        Retrieves real pop hits with high-res album covers and direct audio stream previews.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return cls.CURATED_SPOTIFY_HITS[:limit]

        try:
            url = "https://itunes.apple.com/search"
            params = {
                "term": clean_query,
                "entity": "song",
                "limit": min(25, max(1, limit))
            }
            resp = requests.get(url, params=params, headers={"User-Agent": "FaceBeat-Studio/1.0"}, timeout=6)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                formatted = []
                for it in results:
                    preview_url = it.get("previewUrl")
                    if not preview_url:
                        continue

                    # High resolution artwork (600x600)
                    art = it.get("artworkUrl100", "")
                    if art:
                        art = art.replace("100x100bb.jpg", "600x600bb.jpg")

                    # Genre-based BPM estimation
                    genre = it.get("primaryGenreName", "Pop")
                    bpm = 120
                    if any(g in genre for g in ("Dance", "Electronic", "House", "EDM")):
                        bpm = 128
                    elif any(g in genre for g in ("Hip-Hop", "Rap", "Trap")):
                        bpm = 96
                    elif any(g in genre for g in ("Rock", "Alternative", "Metal")):
                        bpm = 132
                    elif any(g in genre for g in ("R&B", "Soul", "Funk")):
                        bpm = 108
                    elif any(g in genre for g in ("Pop", "Disco")):
                        bpm = 122

                    formatted.append({
                        "id": f"sp_{it.get('trackId')}",
                        "title": it.get("trackName", "Unknown Title"),
                        "artist": it.get("artistName", "Unknown Artist"),
                        "album": it.get("collectionName", "Single / Album"),
                        "bpm": bpm,
                        "duration": int(it.get("trackTimeMillis", 30000) / 1000),
                        "stream_url": preview_url,
                        "cover_art": art or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80",
                        "source": "spotify",
                        "preview_url": preview_url,
                        "spotify_url": it.get("trackViewUrl", "")
                    })
                if formatted:
                    return formatted[:limit]
        except Exception as e:
            logger.warning(f"Public music catalog search error: {e}")

        # Fallback to filtered curated catalog
        matches = [
            t for t in cls.CURATED_SPOTIFY_HITS
            if clean_query.lower() in t["title"].lower()
            or clean_query.lower() in t["artist"].lower()
            or clean_query.lower() in t["album"].lower()
        ]
        return matches[:limit] if matches else cls.CURATED_SPOTIFY_HITS[:limit]

    @classmethod
    def search_tracks(cls, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Searches Spotify for matching tracks with album covers, artist names, and BPM.
        Automatically leverages open public music database when Spotify credentials are not configured.
        """
        clean_query = (query or "").strip()

        token = cls.get_client_credentials_token()
        if token and clean_query:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                params = {"q": clean_query.lower(), "type": "track", "limit": min(20, max(1, limit))}
                resp = requests.get(f"{cls.API_BASE}/search", headers=headers, params=params, timeout=5)
                if resp.status_code == 200:
                    items = resp.json().get("tracks", {}).get("items", [])
                    if items:
                        formatted = []
                        for it in items:
                            images = it.get("album", {}).get("images", [])
                            cover = images[0]["url"] if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80"
                            artists = ", ".join([a["name"] for a in it.get("artists", [])]) or "Unknown Artist"
                            preview = it.get("preview_url")

                            # If Spotify doesn't supply a 30s preview URL, fall back to public catalog stream
                            if not preview:
                                pub = cls.search_public_music_catalog(f"{artists} {it.get('name')}", limit=1)
                                preview = pub[0]["stream_url"] if pub else None

                            if preview:
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
                        if formatted:
                            return formatted[:limit]
            except Exception as e:
                logger.warning(f"Error querying Spotify search API: {e}")

        # When unconfigured or when Spotify doesn't yield streamable results, use open catalog
        if clean_query:
            return cls.search_public_music_catalog(clean_query, limit=limit)

        return cls.CURATED_SPOTIFY_HITS[:limit]

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
