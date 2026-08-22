"""1-Click Character Turnaround Sheet Generator for Gemini Omni Image Roles."""

from typing import Any

from omnimeme.vault import CharacterRole


def build_turnaround_sheet_prompt(
    character: CharacterRole,
    style_preference: str = "",
    reference_image_url: str | None = None,
) -> str:
    """Builds a standardized 4-panel turnaround sheet prompt to anchor character visual likeness."""
    tags = ", ".join(character.aesthetic_tags) if character.aesthetic_tags else "photorealistic, studio lighting"
    style = f" in {style_preference} style" if style_preference else ""
    wardrobe = f", wearing {character.wardrobe}" if character.wardrobe else ""

    ref_anchor = reference_image_url or character.turnaround_sheet_url
    ref_header = ""
    if ref_anchor:
        ref_header = f"### INPUT REFERENCE PHOTO\n@Image1: Reference Character Photo ({ref_anchor})\n\n"

    return (
        f"{ref_header}"
        f"Character turnaround sheet, 4-panel view: front view, side profile view, three-quarter view, back view of "
        f"{character.name} ({character.description}{wardrobe}){style}. "
        f"Clean neutral studio background, consistent character design reference sheet matching @Image1 likeness, {tags}, "
        f"sharp facial details, full body orthographic model sheet."
    )


def generate_turnaround_sheet_config(
    character: CharacterRole,
    style_preference: str = "",
    aspect_ratio: str = "16:9",
    reference_image_url: str | None = None,
) -> dict[str, Any]:
    """Generates the API payload configuration for 1-click image turnaround sheet generation."""
    prompt = build_turnaround_sheet_prompt(character, style_preference, reference_image_url)
    ref_anchor = reference_image_url or character.turnaround_sheet_url

    reference_assets = []
    if ref_anchor:
        reference_assets.append({
            "uri": ref_anchor,
            "mime_type": "image/png",
            "description": "Reference Character Photo (@Image1)",
        })

    return {
        "model": "gemini-3.1-flash-image",
        "prompt": prompt,
        "parameters": {
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
            "quality": "hd",
        },
        "character_role_id": character.role_id,
        "reference_assets": reference_assets,
    }

