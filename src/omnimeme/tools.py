import re
from typing import Any

KEYFRAME_MOTION_PRESETS: dict[str, str] = {
    "dolly_zoom": "Vertigo dolly zoom camera movement.",
    "orbital": "360-degree orbital camera rotation.",
    "whip_pan": "High-speed whip pan transition.",
    "seamless_loop": "Continuous cyclical movement.",
}

CHARACTER_SANITY_MAP: dict[str, str] = {
    "tom cruise": "an intense action hero with a confident grin",
    "elon musk": "an eccentric tech billionaire entrepreneur",
    "taylor swift": "a glamorous pop superstar icon",
    "mickey mouse": "an animated cheerful cartoon rodent mascot",
    "darth vader": "an imposing dark armored villain in a black helmet",
    "iron man": "a high-tech armored superhero in a red and gold powered suit",
    "batman": "a dark nocturnal vigilante hero in a cape and cowl",
    "mario": "a cheerful cartoon plumber in blue overalls and a red cap",
    "spider-man": "an agile acrobatic hero in a red and blue webbed suit",
    "spiderman": "an agile acrobatic hero in a red and blue webbed suit",
    "donald trump": "a high-profile business magnate statesman",
    "barack obama": "a charismatic distinguished statesman",
    "joe biden": "a senior political leader and statesman",
    "superman": "a powerful cape-wearing superhero with an iconic chest emblem",
    "wonder woman": "a heroic warrior princess with a golden tiara and lasso",
}


def sanitize_character_concept(raw_subject: str, theme: str = "cinematic") -> str:
    """Dynamically abstracts real names or trademark names into stylized visual descriptors across any genre/theme."""
    if not raw_subject:
        return ""

    sanitized = raw_subject
    for name_key, descriptor in CHARACTER_SANITY_MAP.items():
        pattern = re.compile(r"\b" + re.escape(name_key) + r"\b", re.IGNORECASE)
        if not pattern.search(sanitized):
            pattern = re.compile(re.escape(name_key), re.IGNORECASE)

        styled_descriptor = descriptor
        if theme and theme.strip().lower() != "cinematic" and theme.strip().lower() not in raw_subject.lower():
            styled_descriptor = f"{descriptor} ({theme.strip()} style)"

        sanitized = pattern.sub(styled_descriptor, sanitized)

    return sanitized



def enhance_video_prompt(
    raw_prompt: str,
    director_notes: str = "",
    character_role: Any | None = None,
    motion_preset: str | None = None,
    theme: str = "cinematic",
) -> dict[str, str]:
    """Enhances a raw user prompt with Omni Flash video directing best practices.

    Args:
        raw_prompt: The user's initial video concept.
        director_notes: Optional additional style or camera guidance.
        character_role: Optional character role configuration or reference.
        motion_preset: Optional camera motion preset key or string directive.
        theme: Optional stylistic theme context for character concept sanitization.
    """
    sanitized_prompt = sanitize_character_concept(raw_prompt.strip(), theme=theme)
    subject = sanitized_prompt
    notes = f" ({director_notes.strip()})" if director_notes.strip() else ""

    role_header = ""
    if character_role and hasattr(character_role, "image_tag"):
        role_header = (
            f"### INPUT ROLES & REFERENCES\n"
            f"{character_role.image_tag}: {character_role.description}\n"
            f"Turnaround Reference: {character_role.turnaround_sheet_url or 'Generated Sheet'}\n\n"
        )

    camera_motion = "35mm lens, smooth steadycam tracking shot at eye level."
    if motion_preset:
        preset_text = KEYFRAME_MOTION_PRESETS.get(motion_preset, motion_preset)
        camera_motion = f"35mm lens, {preset_text}"

    enhanced = (
        f"{role_header}"
        f"[Subject]: {subject}{notes}\n"
        f"[Action & Motion]: Fluid continuous motion, steady temporal pacing.\n"
        f"[Camera Angle & Movement]: {camera_motion}\n"
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
    motion_preset: str | None = None,
    theme: str = "cinematic",
):
    """Yields streaming chunks for enhanced prompt taxonomy."""
    res = enhance_video_prompt(
        raw_prompt,
        director_notes,
        character_role=character_role,
        motion_preset=motion_preset,
        theme=theme,
    )
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
    resolution: str = "720p",
    first_frame_uri: str | None = None,
    last_frame_uri: str | None = None,
    motion_preset: str | None = None,
) -> dict[str, Any]:
    """Generates the API configuration payload for Gemini Omni Flash video generation.

    Args:
        enhanced_prompt: The fully direct-engineered prompt string.
        duration_sec: Duration in seconds (1-10).
        aspect_ratio: Video aspect ratio ('16:9', '9:16', '1:1').
        reference_assets: Optional list of reference images/videos.
        resolution: Video resolution ('360p', '720p', '1080p', '4k').
        first_frame_uri: Optional first frame keyframe GCS URI.
        last_frame_uri: Optional last frame keyframe GCS URI.
        motion_preset: Optional keyframe motion preset name.
    """
    payload: dict[str, Any] = {
        "model": "gemini-omni-1.1-flash-preview",
        "prompt": enhanced_prompt,
        "resolution": resolution,
        "parameters": {
            "duration_seconds": duration_sec,
            "aspect_ratio": aspect_ratio,
            "fps": 24,
            "resolution": resolution,
        },
    }
    if motion_preset:
        payload["parameters"]["motion_preset"] = motion_preset
        payload["motion_preset"] = motion_preset
    if first_frame_uri:
        payload["first_frame_uri"] = first_frame_uri
        payload["parameters"]["first_frame_uri"] = first_frame_uri
    if last_frame_uri:
        payload["last_frame_uri"] = last_frame_uri
        payload["parameters"]["last_frame_uri"] = last_frame_uri
    if reference_assets:
        payload["reference_assets"] = reference_assets
    return payload

