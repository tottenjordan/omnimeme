"""Free-form Text Widget UI Handler for Omni Flash Video Generation."""

from dataclasses import dataclass
from typing import Any

from omnimeme.agent import OmniDirectorAgent


@dataclass
class FreeformInput:
    raw_prompt: str
    director_style_preference: str = ""

    def validate(self) -> bool:
        return bool(self.raw_prompt and self.raw_prompt.strip())


def process_freeform_request(input_data: FreeformInput, agent: OmniDirectorAgent) -> dict[str, Any]:
    """Processes a raw free-form text input widget request through the ADK Omni Director agent."""
    if not input_data.validate():
        return {
            "interface": "freeform_widget",
            "status": "error",
            "error_message": "Prompt cannot be empty.",
        }

    result = agent.run(
        user_prompt=input_data.raw_prompt, director_notes=input_data.director_style_preference
    )
    return {
        "interface": "freeform_widget",
        "status": "success",
        "input": input_data,
        "result": result,
    }
