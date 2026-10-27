import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Base Directory of FaceBeat-Studio
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    # App Settings
    APP_NAME: str = "FaceBeat-Studio"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # AI & Agents
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_AGENT_MODEL: str = "gemini-2.5-flash"

    # Spotify API (Optional)
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/api/spotify/callback")

    # Jamendo Music API (Free Tier)
    JAMENDO_CLIENT_ID: str = os.getenv("JAMENDO_CLIENT_ID", "56d30c95")

    # Storage Paths
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    AUDIO_DIR: Path = BASE_DIR / "app" / "static" / "audio"
    MEDIA_DIR: Path = BASE_DIR / "app" / "static" / "media"
    CLIPS_DIR: Path = BASE_DIR / "app" / "static" / "media" / "clips"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_PATH: Path = BASE_DIR / "data" / "facebeat.db"

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        self.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        self.CLIPS_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
