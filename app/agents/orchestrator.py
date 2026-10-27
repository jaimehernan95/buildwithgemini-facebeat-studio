import json
import logging
from typing import Dict, Any, Optional
from google.antigravity import Agent, LocalAgentConfig, types
from app.config import settings
from app.agents.rhythm_analyzer import get_rhythm_analyzer_config, analyze_audio_track
from app.agents.audio_safety import get_audio_safety_config, check_audio_copyright_safety, get_safe_audio_library
from app.agents.social_clipper import get_social_clipper_config, render_gameplay_social_clip

logger = logging.getLogger("facebeat.orchestrator")


class FaceBeatOrchestrator:
    """Central Multi-Agent Orchestrator managing RhythmAnalyzerAgent,
    AudioSafetyAgent, and SocialClipperAgent via Google Antigravity SDK.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.rhythm_subagent = get_rhythm_analyzer_config()
        self.safety_subagent = get_audio_safety_config()
        self.clipper_subagent = get_social_clipper_config()

        self.agent_config = self._build_config()

    def _build_config(self) -> LocalAgentConfig:
        """Builds the LocalAgentConfig with all three subagents and autonomous capabilities."""
        config_kwargs: Dict[str, Any] = {
            "subagents": [
                self.rhythm_subagent,
                self.safety_subagent,
                self.clipper_subagent,
            ],
            "capabilities": types.CapabilitiesConfig(
                enable_subagents=True,
                max_subagent_depth=2,
                allowed_subagents=[
                    "RhythmAnalyzerAgent",
                    "AudioSafetyAgent",
                    "SocialClipperAgent",
                ],
            ),
            "system_instructions": (
                "You are FaceBeat-Studio Orchestrator, coordinating real-time rhythm game operations. "
                "You coordinate three specialized subagents: "
                "1) RhythmAnalyzerAgent: Generates beat maps and frequency timings for visual targets. "
                "2) AudioSafetyAgent: Validates Spotify licensing, manages royalty-free lofi piano and beat loops. "
                "3) SocialClipperAgent: Produces vertical 9:16 gameplay clips with HUD watermarks for TikTok/Reels."
            ),
        }

        if self.api_key:
            config_kwargs["api_key"] = self.api_key

        return LocalAgentConfig(**config_kwargs)

    async def chat(self, prompt: str) -> str:
        """Sends an interactive instruction or task to the Antigravity Agent and subagents."""
        # 1. Try Google Antigravity Agent if api_key is configured
        if self.api_key:
            try:
                async with Agent(self.agent_config) as agent:
                    response = await agent.chat(prompt)
                    return await response.text()
            except Exception as e:
                logger.error("Antigravity agent chat error: %s", e)

        # 2. Try Google Vertex AI Gemini (integrated in GCP environment)
        try:
            import os
            from google import genai
            project = os.getenv("GOOGLE_CLOUD_PROJECT") or "qwiklabs-gcp-04-e7ff715cb28f"
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            client = genai.Client(vertexai=True, project=project, location=location)
            system_prompt = (
                "You are FaceBeat-Studio Orchestrator, coordinating real-time rhythm game operations. "
                "You coordinate three specialized subagents: "
                "1) RhythmAnalyzerAgent: Generates beat maps, BPM, and facial expression targets (Jaw, Smile, Brow). "
                "2) AudioSafetyAgent: Validates copyright status and royalty-free lofi/synth tracks. "
                "3) SocialClipperAgent: Produces 9:16 vertical gameplay highlights for TikTok/Reels. "
                "Be energetic, concise, and helpful with gameplay tips, custom song ideas, or beat tracking."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=dict(system_instruction=system_prompt),
            )
            if response.text:
                return response.text
        except Exception as e:
            logger.warning("Vertex AI Gemini chat fallback notice: %s", e)

        return (
            "[Offline Mode] Deterministic agent tools are active and handling all game logic directly."
        )

    # Direct Deterministic Facades for FastAPI endpoints
    def analyze_track(self, filename: str, difficulty: str = "normal") -> Dict[str, Any]:
        """Dispatches track analysis via RhythmAnalyzerAgent."""
        raw = analyze_audio_track(filename, difficulty=difficulty)
        return json.loads(raw)

    def check_safety(self, track_title: str, artist: str = "") -> Dict[str, Any]:
        """Dispatches copyright safety check via AudioSafetyAgent."""
        raw = check_audio_copyright_safety(track_title, artist=artist)
        return json.loads(raw)

    def get_safe_tracks(self) -> Dict[str, Any]:
        """Retrieves verified safe music catalog via AudioSafetyAgent."""
        raw = get_safe_audio_library()
        return json.loads(raw)

    def render_clip(
        self,
        video_filename: str,
        score: int,
        max_combo: int,
        track_title: str,
        player_name: str,
        audio_filename: str = "",
    ) -> Dict[str, Any]:
        """Dispatches vertical 9:16 clip generation via SocialClipperAgent."""
        raw = render_gameplay_social_clip(
            video_filename=video_filename,
            score=score,
            max_combo=max_combo,
            track_title=track_title,
            player_name=player_name,
            audio_filename=audio_filename,
        )
        return json.loads(raw)


# Global orchestrator singleton instance
orchestrator = FaceBeatOrchestrator()
