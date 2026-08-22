"""Tests for Gemini Omni Flash Video Execution Engine."""

from omnimeme.engine import (
    GenerationResult,
    OmniFlashExecutionEngine,
    parse_guardrail_error_guidance,
)


def test_generation_result_creation():
    res = GenerationResult(
        interaction_thread_id="turn_123",
        video_url="/static/rendered/test.mp4",
        status="completed",
    )
    assert res.interaction_thread_id == "turn_123"
    assert res.video_url == "/static/rendered/test.mp4"
    assert res.synth_id_watermark == "SYNTHID_C2PA_VERIFIED"


def test_guardrail_error_guidance():
    guidance = parse_guardrail_error_guidance("Input blocked: real people's names or likenesses")
    assert "real_people_likeness" in guidance["triggers"]
    assert len(guidance["suggested_actions"]) >= 1


def test_execution_engine_generate_video(tmp_path):
    engine = OmniFlashExecutionEngine(mock_mode=True)
    config = {
        "model": "gemini-omni-flash-preview",
        "prompt": "A futuristic motorcycle racing down a neon highway",
        "parameters": {"duration_seconds": 3, "aspect_ratio": "16:9"},
    }
    result = engine.generate_video(config, output_filename="test_moto.mp4")
    assert result.status == "completed"
    assert result.video_url.startswith("/static/rendered/")
    assert result.duration_seconds == 3
