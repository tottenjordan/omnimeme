"""Tests for 1-Click Character Turnaround Sheet Prompt Generator."""

from omnimeme.turnaround import build_turnaround_sheet_prompt, generate_turnaround_sheet_config
from omnimeme.vault import CharacterRole


def test_build_turnaround_sheet_prompt():
    char = CharacterRole(
        role_id="char_samurai_01",
        name="Cyber Samurai",
        description="Cyberpunk samurai with glowing visor and dark obsidian armor",
        aesthetic_tags=["cyberpunk", "3D render"],
    )
    prompt = build_turnaround_sheet_prompt(char)
    assert "Character turnaround sheet" in prompt
    assert "4-panel view" in prompt
    assert "front view" in prompt
    assert "side profile view" in prompt
    assert "three-quarter view" in prompt
    assert "back view" in prompt
    assert "Cyberpunk samurai with glowing visor" in prompt


def test_generate_turnaround_sheet_config():
    char = CharacterRole(
        role_id="char_samurai_01",
        name="Cyber Samurai",
        description="Cyberpunk samurai with glowing visor",
    )
    cfg = generate_turnaround_sheet_config(char)
    assert cfg["model"] == "gemini-3.1-flash-image"
    assert "4-panel view" in cfg["prompt"]
    assert cfg["parameters"]["aspect_ratio"] == "16:9"


def test_build_turnaround_sheet_prompt_with_reference_image():
    from omnimeme.turnaround import build_turnaround_sheet_prompt, generate_turnaround_sheet_config
    from omnimeme.vault import CharacterRole

    char = CharacterRole(
        role_id="char_samurai_01",
        name="Cyber Samurai",
        description="Cyberpunk samurai with glowing visor",
    )
    ref_url = "gs://omnimeme-vault/references/samurai_portrait.png"

    prompt = build_turnaround_sheet_prompt(char, reference_image_url=ref_url)
    assert "@Image1: Reference Character Photo" in prompt
    assert "gs://omnimeme-vault/references/samurai_portrait.png" in prompt

    cfg = generate_turnaround_sheet_config(char, reference_image_url=ref_url)
    assert cfg["reference_assets"][0]["uri"] == ref_url
    assert cfg["reference_assets"][0]["description"] == "Reference Character Photo (@Image1)"

