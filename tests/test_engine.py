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
        "model": "gemini-omni-1.1-flash",
        "prompt": "A futuristic motorcycle racing down a neon highway",
        "parameters": {"duration_seconds": 3, "aspect_ratio": "16:9", "resolution": "1080p"},
    }
    result = engine.generate_video(
        config,
        output_filename="test_moto.mp4",
        resolution="1080p",
        first_frame_uri="gs://bucket/start.png",
        last_frame_uri="gs://bucket/end.png",
    )
    assert result.status == "completed"
    assert result.video_url.startswith("/static/rendered/")
    assert result.duration_seconds == 3


def test_engine_default_mock_mode():
    engine = OmniFlashExecutionEngine()
    assert engine.mock_mode is False
    assert engine.model == "gemini-omni-1.1-flash"


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
            assert kwargs["model"] == "gemini-omni-1.1-flash"
            assert kwargs["input"] == [{"type": "text", "text": "Test prompt"}]
            assert kwargs.get("previous_interaction_id") == "prev_turn_1"
            assert "first_frame_uri" not in kwargs
            assert "last_frame_uri" not in kwargs
            assert "resolution" not in kwargs
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
    assert res.generation_mode == "LIVE_GEMINI_OMNI_1_1_FLASH"


def test_concatenate_storyboard_videos_success():
    import os

    from omnimeme.engine import concatenate_storyboard_videos, ensure_rendered_video

    url1 = "/static/rendered/test_scene_1.mp4"
    url2 = "/static/rendered/test_scene_2.mp4"
    ensure_rendered_video(url1, prompt="Scene 1", duration=2)
    ensure_rendered_video(url2, prompt="Scene 2", duration=2)

    master_url = concatenate_storyboard_videos([url1, url2], output_filename="test_master_out.mp4")
    assert master_url.startswith("/static/rendered/")
    assert master_url.endswith("test_master_out.mp4")
    rel_path = master_url.lstrip("/")
    assert os.path.exists(rel_path)
    assert os.path.getsize(rel_path) > 0


def test_concatenate_storyboard_videos_empty_list():
    import pytest

    from omnimeme.engine import concatenate_storyboard_videos

    with pytest.raises(ValueError, match="video_urls list cannot be empty"):
        concatenate_storyboard_videos([])


def test_concatenate_storyboard_videos_full_url():
    import os

    from omnimeme.engine import concatenate_storyboard_videos, ensure_rendered_video

    url1 = "http://localhost:8000/static/rendered/full_url_scene1.mp4"
    url2 = "http://localhost:8000/static/rendered/full_url_scene2.mp4"
    ensure_rendered_video("/static/rendered/full_url_scene1.mp4", prompt="Scene 1", duration=2)
    ensure_rendered_video("/static/rendered/full_url_scene2.mp4", prompt="Scene 2", duration=2)

    master_url = concatenate_storyboard_videos([url1, url2], output_filename="full_url_out.mp4")
    assert master_url.startswith("/static/rendered/master_")
    assert os.path.exists(master_url.lstrip("/"))


def test_concatenate_storyboard_videos_enforce_master_prefix():
    from omnimeme.engine import concatenate_storyboard_videos, ensure_rendered_video

    url = "/static/rendered/scene_prefix.mp4"
    ensure_rendered_video(url, prompt="Scene", duration=2)

    master_url = concatenate_storyboard_videos([url], output_filename="custom_feature.mp4")
    assert master_url == "/static/rendered/master_custom_feature.mp4"
