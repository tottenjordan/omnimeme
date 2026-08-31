"""Guided Experience UI Handler for Omni Flash Video Generation."""

from dataclasses import dataclass, field
from typing import Any

from omnimeme.agent import OmniDirectorAgent


@dataclass
class MediaAttachment:
    """Dataclass representing a reference image (.png, .jpg) or video (.mp4)."""

    uri: str
    mime_type: str
    description: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "uri": self.uri,
            "mime_type": self.mime_type,
            "description": self.description,
        }


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
    resolution: str = "720p"
    first_frame_uri: str | None = None
    last_frame_uri: str | None = None
    reference_images: list[MediaAttachment] = field(default_factory=list)
    reference_videos: list[MediaAttachment] = field(default_factory=list)
    motion_preset: str | None = None

    def validate(self) -> bool:
        return bool(self.subject and self.subject.strip())

    def get_all_reference_assets(self) -> list[dict[str, str]]:
        assets = []
        for img in self.reference_images:
            assets.append(img.to_dict())
        for vid in self.reference_videos:
            assets.append(vid.to_dict())
        return assets

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

        ref_parts = []
        for img in self.reference_images:
            desc = img.description or "Image Reference"
            ref_parts.append(f"{desc} ({img.uri})")
        for vid in self.reference_videos:
            desc = vid.description or "Video Reference"
            ref_parts.append(f"{desc} ({vid.uri})")

        if ref_parts:
            parts.append(f"Reference Attachments: {', '.join(ref_parts)}")

        return " | ".join(parts)


def process_guided_request(
    input_data: GuidedPromptInput, agent: OmniDirectorAgent, character_role: Any | None = None
) -> dict[str, Any]:
    """Processes a guided structured input form through the ADK Omni Director agent."""
    if not input_data.validate():
        return {
            "interface": "guided_experience",
            "status": "error",
            "error_message": "Subject cannot be empty.",
        }

    raw_directive = input_data.to_raw_directive()
    reference_assets = input_data.get_all_reference_assets()
    result = agent.run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {input_data.aspect_ratio}, Duration: {input_data.duration_sec}s",
        duration_sec=input_data.duration_sec,
        aspect_ratio=input_data.aspect_ratio,
        resolution=input_data.resolution,
        first_frame_uri=input_data.first_frame_uri,
        last_frame_uri=input_data.last_frame_uri,
        reference_assets=reference_assets,
        character_role=character_role,
        motion_preset=input_data.motion_preset,
    )
    return {
        "interface": "guided_experience",
        "status": "success",
        "input": input_data,
        "result": result,
    }
