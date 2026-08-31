"""Tests for OmniMeme v2 Feature Expansion and Generalized Theme/Name Sanitizer."""

from omnimeme.engine import parse_guardrail_error_guidance
from omnimeme.tools import (
    KEYFRAME_MOTION_PRESETS,
    enhance_video_prompt,
    generate_video_config,
    sanitize_character_concept,
)


def test_keyframe_motion_presets_dictionary():
    assert "dolly_zoom" in KEYFRAME_MOTION_PRESETS
    assert "orbital" in KEYFRAME_MOTION_PRESETS
    assert "whip_pan" in KEYFRAME_MOTION_PRESETS
    assert "seamless_loop" in KEYFRAME_MOTION_PRESETS

    assert KEYFRAME_MOTION_PRESETS["dolly_zoom"] == "Vertigo dolly zoom camera movement."
    assert KEYFRAME_MOTION_PRESETS["orbital"] == "360-degree orbital camera rotation."
    assert KEYFRAME_MOTION_PRESETS["whip_pan"] == "High-speed whip pan transition."
    assert KEYFRAME_MOTION_PRESETS["seamless_loop"] == "Continuous cyclical movement."


def test_sanitize_character_concept():
    # Celebrity / Real name sanitization
    sanitized_tom = sanitize_character_concept("Tom Cruise riding a motorcycle", theme="cyberpunk")
    assert "Tom Cruise" not in sanitized_tom
    assert "an intense action hero with a confident grin" in sanitized_tom

    # Trademark / Cartoon name sanitization
    sanitized_mickey = sanitize_character_concept("Mickey Mouse exploring a castle")
    assert "Mickey Mouse" not in sanitized_mickey
    assert "rodent mascot" in sanitized_mickey

    # Passthrough for generic prompt
    generic = sanitize_character_concept("A futuristic sports car on a highway")
    assert generic == "A futuristic sports car on a highway"


def test_enhance_video_prompt_with_motion_preset_and_sanitization():
    res = enhance_video_prompt(
        raw_prompt="Elon Musk presenting a futuristic rocket launch",
        motion_preset="orbital",
        theme="sci-fi",
    )
    prompt_text = res["enhanced_prompt"]
    assert "Elon Musk" not in prompt_text
    assert "an eccentric tech billionaire entrepreneur" in prompt_text
    assert "360-degree orbital camera rotation." in prompt_text


def test_generate_video_config_with_360p_and_motion_preset():
    cfg = generate_video_config(
        enhanced_prompt="Sanitized concept video",
        resolution="360p",
        motion_preset="whip_pan",
    )
    assert cfg["resolution"] == "360p"
    assert cfg["parameters"]["resolution"] == "360p"
    assert cfg["parameters"]["motion_preset"] == "whip_pan"


def test_engine_guardrail_guidance_sanitization():
    guidance = parse_guardrail_error_guidance(
        "Safety block: real people Taylor Swift mentioned",
        raw_subject="Taylor Swift singing at concert",
    )
    assert "real_people_likeness" in guidance["triggers"]
    assert "sanitized_concept" in guidance
    assert "a glamorous pop superstar icon" in guidance["sanitized_concept"]
