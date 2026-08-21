"""Guided Experience UI Handler for Omni Flash Video Generation."""

from dataclasses import dataclass
from typing import Any

from omnimeme.agent import OmniDirectorAgent


@dataclass
class GuidedPromptInput:
    subject: str
    action: str = ""
    camera: str = ""
    lighting: str = ""
    style: str = ""
    audio: str = ""
    duration_sec: int = 5
    aspect_ratio: str = "16:9"

    def validate(self) -> bool:
        return bool(self.subject and self.subject.strip())

    def to_raw_directive(self) -> str:
        parts = [f"Subject: {self.subject}"]
        if self.action:
            parts.append(f"Action: {self.action}")
        if self.camera:
            parts.append(f"Camera: {self.camera}")
        if self.lighting:
            parts.append(f"Lighting: {self.lighting}")
        if self.style:
            parts.append(f"Style: {self.style}")
        if self.audio:
            parts.append(f"Audio: {self.audio}")
        return " | ".join(parts)


def process_guided_request(
    input_data: GuidedPromptInput, agent: OmniDirectorAgent
) -> dict[str, Any]:
    """Processes a guided structured input form through the ADK Omni Director agent."""
    if not input_data.validate():
        return {
            "interface": "guided_experience",
            "status": "error",
            "error_message": "Subject cannot be empty.",
        }

    raw_directive = input_data.to_raw_directive()
    result = agent.run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {input_data.aspect_ratio}, Duration: {input_data.duration_sec}s",
        duration_sec=input_data.duration_sec,
        aspect_ratio=input_data.aspect_ratio,
    )
    return {
        "interface": "guided_experience",
        "status": "success",
        "input": input_data,
        "result": result,
    }
