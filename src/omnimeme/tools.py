"""Tools for prompt enhancement and Gemini Omni Flash video configuration."""

from typing import Any


def enhance_video_prompt(
    raw_prompt: str,
    director_notes: str = "",
    character_role: Any | None = None,
) -> dict[str, str]:
    """Enhances a raw user prompt with Omni Flash video directing best practices.

    Args:
        raw_prompt: The user's initial video concept.
        director_notes: Optional additional style or camera guidance.
        character_role: Optional character role configuration or reference.
    """
    subject = raw_prompt.strip()
    notes = f" ({director_notes.strip()})" if director_notes.strip() else ""

    role_header = ""
    if character_role and hasattr(character_role, "image_tag"):
        role_header = (
            f"### INPUT ROLES & REFERENCES\n"
            f"{character_role.image_tag}: {character_role.description}\n"
            f"Turnaround Reference: {character_role.turnaround_sheet_url or 'Generated Sheet'}\n\n"
        )

    enhanced = (
        f"{role_header}"
        f"[Subject]: {subject}{notes}\n"
        f"[Action & Motion]: Fluid continuous motion, steady temporal pacing.\n"
        f"[Camera Angle & Movement]: 35mm lens, smooth steadycam tracking shot at eye level.\n"
        f"[Lighting & Atmosphere]: Natural volumetric lighting with cinematic color grade.\n"
        f"[Style & Aesthetics]: Photorealistic, 4K film crispness.\n"
        f"[Audio Cues]: Immersive ambient atmospheric sound matching visual action."
    )
    return {
        "raw_prompt": raw_prompt,
        "enhanced_prompt": enhanced,
    }


def stream_enhance_video_prompt(
    raw_prompt: str,
    director_notes: str = "",
    character_role: Any | None = None,
):
    """Yields streaming chunks for enhanced prompt taxonomy."""
    res = enhance_video_prompt(raw_prompt, director_notes, character_role=character_role)
    text = res["enhanced_prompt"]
    # Chunk by lines to provide natural streaming animation
    lines = text.split("\n")
    for i, line in enumerate(lines):
        chunk = line + ("\n" if i < len(lines) - 1 else "")
        yield chunk


def generate_video_config(
    enhanced_prompt: str,
    duration_sec: int = 5,
    aspect_ratio: str = "16:9",
    reference_assets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generates the API configuration payload for Gemini Omni Flash video generation.

    Args:
        enhanced_prompt: The fully direct-engineered prompt string.
        duration_sec: Duration in seconds (1-10).
        aspect_ratio: Video aspect ratio ('16:9', '9:16', '1:1').
        reference_assets: Optional list of reference images/videos.
    """
    payload: dict[str, Any] = {
        "model": "gemini-omni-flash-preview",
        "prompt": enhanced_prompt,
        "parameters": {
            "duration_seconds": duration_sec,
            "aspect_ratio": aspect_ratio,
            "fps": 24,
        },
    }
    if reference_assets:
        payload["reference_assets"] = reference_assets
    return payload
