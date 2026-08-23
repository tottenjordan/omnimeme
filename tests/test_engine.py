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


def test_engine_default_mock_mode():
    engine = OmniFlashExecutionEngine()
    assert engine.mock_mode is False


def test_execution_engine_interactions_api_mock(monkeypatch, tmp_path):
    import base64

    fake_video_bytes = b"FAKE_MP4_HEADER_DATA"
    fake_b64 = base64.b64encode(fake_video_bytes).decode("utf-8")

    class FakeOutputVideo:
        data = fake_b64

    class FakeInteraction:
        id = "turn_live_999"
        output_video = FakeOutputVideo()

    class FakeInteractionsClient:
        def create(self, **kwargs):
            assert kwargs["model"] == "gemini-omni-flash-preview"
            assert kwargs["input"] == "Test prompt"
            assert kwargs.get("previous_interaction_id") == "prev_turn_1"
            return FakeInteraction()

    class FakeGenAIClient:
        interactions = FakeInteractionsClient()

    fake_genai = type("FakeGenAI", (), {"Client": lambda self=None, **k: FakeGenAIClient()})()

    import omnimeme.engine
    monkeypatch.setattr(omnimeme.engine, "genai", fake_genai)

    engine = OmniFlashExecutionEngine(mock_mode=False)
    config = {"prompt": "Test prompt"}
    res = engine.generate_video(
        config,
        output_filename="live_test.mp4",
        previous_interaction_id="prev_turn_1",
    )

    assert res.status == "completed"
    assert res.interaction_thread_id == "turn_live_999"
    assert res.generation_mode == "LIVE_GEMINI_OMNI_FLASH"

