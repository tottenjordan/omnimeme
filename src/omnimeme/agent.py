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
        model: str = "gemini-omni-1.1-flash",
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
        resolution: str = "720p",
        first_frame_uri: str | None = None,
        last_frame_uri: str | None = None,
        reference_assets: list[dict[str, Any]] | None = None,
        character_role: Any | None = None,
        motion_preset: str | None = None,
        theme: str = "cinematic",
        dialogue_text: str = "",
        sound_effects: str = "",
        music_score: str = "",
        mute_dialogue: bool = False,
        no_music: bool = False,
    ) -> dict[str, Any]:
        if character_role and getattr(character_role, "turnaround_sheet_url", None):
            ref_asset = {
                "uri": character_role.turnaround_sheet_url,
                "mime_type": "image/png",
                "description": f"{character_role.name} Turnaround Sheet (@Image1)",
            }
            if reference_assets is None:
                reference_assets = []
            else:
                reference_assets = list(reference_assets)
            reference_assets.append(ref_asset)

        enhanced = enhance_video_prompt(
            user_prompt,
            director_notes,
            character_role=character_role,
            motion_preset=motion_preset,
            theme=theme,
            dialogue_text=dialogue_text,
            sound_effects=sound_effects,
            music_score=music_score,
            mute_dialogue=mute_dialogue,
            no_music=no_music,
        )
        config = generate_video_config(
            enhanced["enhanced_prompt"],
            duration_sec=duration_sec,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            first_frame_uri=first_frame_uri,
            last_frame_uri=last_frame_uri,
            reference_assets=reference_assets,
            motion_preset=motion_preset,
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
        resolution: str = "720p",
        first_frame_uri: str | None = None,
        last_frame_uri: str | None = None,
        reference_assets: list[dict[str, Any]] | None = None,
        character_role: Any | None = None,
        motion_preset: str | None = None,
        theme: str = "cinematic",
        dialogue_text: str = "",
        sound_effects: str = "",
        music_score: str = "",
        mute_dialogue: bool = False,
        no_music: bool = False,
    ):
        """Yields SSE events for token streaming and final result payload."""
        import json

        from omnimeme.tools import stream_enhance_video_prompt

        if character_role and getattr(character_role, "turnaround_sheet_url", None):
            ref_asset = {
                "uri": character_role.turnaround_sheet_url,
                "mime_type": "image/png",
                "description": f"{character_role.name} Turnaround Sheet (@Image1)",
            }
            if reference_assets is None:
                reference_assets = []
            else:
                reference_assets = list(reference_assets)
            reference_assets.append(ref_asset)

        accumulated = []
        for chunk in stream_enhance_video_prompt(
            user_prompt,
            director_notes,
            character_role=character_role,
            motion_preset=motion_preset,
            theme=theme,
            dialogue_text=dialogue_text,
            sound_effects=sound_effects,
            music_score=music_score,
            mute_dialogue=mute_dialogue,
            no_music=no_music,
        ):
            accumulated.append(chunk)
            token_event = {"type": "token", "chunk": chunk}
            yield f"data: {json.dumps(token_event)}\n\n"

        full_prompt = "".join(accumulated)
        config = generate_video_config(
            full_prompt,
            duration_sec=duration_sec,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            first_frame_uri=first_frame_uri,
            last_frame_uri=last_frame_uri,
            reference_assets=reference_assets,
            motion_preset=motion_preset,
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
