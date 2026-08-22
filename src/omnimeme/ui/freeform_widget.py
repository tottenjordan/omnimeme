"""Free-form Text Widget UI Handler for Omni Flash Video Generation."""

from dataclasses import dataclass, field
from typing import Any

from omnimeme.agent import OmniDirectorAgent
from omnimeme.ui.guided_experience import MediaAttachment


@dataclass
class FreeformInput:
    raw_prompt: str
    director_style_preference: str = ""
    reference_images: list[MediaAttachment] = field(default_factory=list)
    reference_videos: list[MediaAttachment] = field(default_factory=list)

    def validate(self) -> bool:
        return bool(self.raw_prompt and self.raw_prompt.strip())

    def get_all_reference_assets(self) -> list[dict[str, str]]:
        assets = []
        for img in self.reference_images:
            assets.append(img.to_dict())
        for vid in self.reference_videos:
            assets.append(vid.to_dict())
        return assets


def process_freeform_request(
    input_data: FreeformInput, agent: OmniDirectorAgent, character_role: Any | None = None
) -> dict[str, Any]:
    """Processes a raw free-form text input widget request through the ADK Omni Director agent."""
    if not input_data.validate():
        return {
            "interface": "freeform_widget",
            "status": "error",
            "error_message": "Prompt cannot be empty.",
        }

    reference_assets = input_data.get_all_reference_assets()
    result = agent.run(
        user_prompt=input_data.raw_prompt,
        director_notes=input_data.director_style_preference,
        reference_assets=reference_assets,
        character_role=character_role,
    )
    return {
        "interface": "freeform_widget",
        "status": "success",
        "input": input_data,
        "result": result,
    }
