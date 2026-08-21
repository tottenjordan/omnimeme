"""ADK Agent Setup for Omni Flash Video Directing."""

from typing import Any

from omnimeme.client import get_platform_client
from omnimeme.prompts import OMNI_FLASH_DIRECTING_INSTR
from omnimeme.tools import enhance_video_prompt, generate_video_config


class OmniDirectorAgent:
    """ADK Agent representation for Omni Flash Video Directing using agentplatform.Client."""

    def __init__(
        self,
        name: str = "omni_director",
        model: str = "gemini-omni-flash-preview",
        project_id: str | None = None,
        location: str | None = "us-central1",
    ):
        self.name = name
        self.model = model
        self.client = get_platform_client(project_id, location)
        self.instruction = OMNI_FLASH_DIRECTING_INSTR
        self.tools = [enhance_video_prompt, generate_video_config]

    def run(
        self,
        user_prompt: str,
        director_notes: str = "",
        duration_sec: int = 5,
        aspect_ratio: str = "16:9",
    ) -> dict[str, Any]:
        enhanced = enhance_video_prompt(user_prompt, director_notes)
        config = generate_video_config(
            enhanced["enhanced_prompt"], duration_sec=duration_sec, aspect_ratio=aspect_ratio
        )
        return {
            "agent_name": self.name,
            "model": self.model,
            "enhanced_prompt": enhanced["enhanced_prompt"],
            "video_config": config,
        }

    def stream_run(
        self,
        user_prompt: str,
        director_notes: str = "",
        duration_sec: int = 5,
        aspect_ratio: str = "16:9",
    ):
        """Yields SSE events for token streaming and final result payload."""
        import json

        from omnimeme.tools import stream_enhance_video_prompt

        accumulated = []
        for chunk in stream_enhance_video_prompt(user_prompt, director_notes):
            accumulated.append(chunk)
            token_event = {"type": "token", "chunk": chunk}
            yield f"data: {json.dumps(token_event)}\n\n"

        full_prompt = "".join(accumulated)
        config = generate_video_config(
            full_prompt, duration_sec=duration_sec, aspect_ratio=aspect_ratio
        )
        done_event = {
            "type": "done",
            "result": {
                "agent_name": self.name,
                "model": self.model,
                "enhanced_prompt": full_prompt,
                "video_config": config,
            },
        }
        yield f"data: {json.dumps(done_event)}\n\n"


def create_omni_director_agent() -> OmniDirectorAgent:
    """Factory to instantiate the Omni Director ADK agent."""
    return OmniDirectorAgent()
