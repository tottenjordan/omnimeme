"""Tests for Chained Multi-Scene Extension Engine (Zero Visual Drift)."""

import pytest
from fastapi.testclient import TestClient

from omnimeme.engine import GenerationResult, OmniFlashExecutionEngine
from omnimeme.scriptwriter import ScriptwriterAgent
from omnimeme.server.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_format_chained_scene_prompt_scene_1():
    agent = ScriptwriterAgent()
    prompt = agent.format_chained_scene_prompt(
        scene_number=1,
        visual_description="A cyberpunk samurai steps out into rainy streets.",
        camera_instruction="Wide tracking push-in shot.",
    )
    assert prompt == "A cyberpunk samurai steps out into rainy streets."


def test_format_chained_scene_prompt_scene_2_plus():
    agent = ScriptwriterAgent()
    prompt_scene_2 = agent.format_chained_scene_prompt(
        scene_number=2,
        visual_description="The samurai draws a plasma katana and enters a neon alley.",
        camera_instruction="Medium orbital tracking shot.",
    )
    assert "Extend this video continuously:" in prompt_scene_2
    assert "Maintain exact character likeness, wardrobe details, lighting palette" in prompt_scene_2
    assert "Keep the visual style and world physics identical." in prompt_scene_2
    assert "Camera: Medium orbital tracking shot." in prompt_scene_2

    prompt_scene_3 = agent.format_chained_scene_prompt(
        scene_number=3,
        visual_description="The samurai inspects glowing cybernetic blueprints.",
    )
    assert "Extend this video continuously:" in prompt_scene_3
    assert "Keep the visual style and world physics identical." in prompt_scene_3


def test_generate_storyboard_includes_chained_flags_and_prompts():
    agent = ScriptwriterAgent()
    res = agent.generate_storyboard(
        concept="A space explorer entering an alien monolith",
        scene_count=3,
        style_preference="Sci-fi cinematic IMAX",
    )
    assert len(res["scenes"]) == 3
    for scene in res["scenes"]:
        assert scene["is_chained"] is True
        assert "video_config" in scene

    # Scene 1 prompt is standard; Scene 2 and 3 video configs have extension directives
    scene1_prompt = res["scenes"][0]["video_config"]["prompt"]
    scene2_prompt = res["scenes"][1]["video_config"]["prompt"]
    scene3_prompt = res["scenes"][2]["video_config"]["prompt"]

    assert "Extend this video continuously:" not in scene1_prompt
    assert "Extend this video continuously:" in scene2_prompt
    assert "Extend this video continuously:" in scene3_prompt


def test_generate_mashup_storyboard_includes_chained_flags():
    agent = ScriptwriterAgent()
    res = agent.generate_mashup_storyboard(
        character_a_id="space_lord",
        character_b_id="chef_supreme",
        mashup_genre="Sci-Fi Reality Cooking Show",
        scene_count=4,
    )
    assert len(res["scenes"]) == 4
    for scene in res["scenes"]:
        assert scene["is_chained"] is True

    # Scene 1 is base prompt, scenes 2-4 are chained extensions
    assert "Extend this video continuously:" not in res["scenes"][0]["video_config"]["prompt"]
    assert "Extend this video continuously:" in res["scenes"][1]["video_config"]["prompt"]
    assert "Extend this video continuously:" in res["scenes"][2]["video_config"]["prompt"]
    assert "Extend this video continuously:" in res["scenes"][3]["video_config"]["prompt"]


def test_render_chained_storyboard_sequential_interactions():
    engine = OmniFlashExecutionEngine(mock_mode=True)

    scenes = [
        {"scene_number": 1, "video_config": {"prompt": "Scene 1 base"}},
        {"scene_number": 2, "video_config": {"prompt": "Scene 2 extension"}},
        {"scene_number": 3, "video_config": {"prompt": "Scene 3 extension"}},
    ]

    recorded_calls = []

    def mock_generate_video(
        config, output_filename=None, previous_interaction_id=None, resolution="720p", **kwargs
    ):
        recorded_calls.append(
            {
                "prompt": config.get("prompt"),
                "previous_interaction_id": previous_interaction_id,
            }
        )
        turn_num = len(recorded_calls)
        return GenerationResult(
            interaction_thread_id=f"interaction_turn_{turn_num}",
            video_url=f"/static/rendered/scene_{turn_num}.mp4",
            duration_seconds=5,
            status="completed",
        )

    engine.generate_video = mock_generate_video

    rendered = engine.render_chained_storyboard(scenes, resolution="720p")

    assert len(rendered) == 3
    assert len(recorded_calls) == 3

    # Turn 1 passes previous_interaction_id=None
    assert recorded_calls[0]["previous_interaction_id"] is None
    # Turn 2 passes previous_interaction_id="interaction_turn_1"
    assert recorded_calls[1]["previous_interaction_id"] == "interaction_turn_1"
    # Turn 3 passes previous_interaction_id="interaction_turn_2"
    assert recorded_calls[2]["previous_interaction_id"] == "interaction_turn_2"

    for i, sc in enumerate(rendered, start=1):
        assert sc["turn_number"] == i
        assert sc["interaction_id"] == f"interaction_turn_{i}"
        assert sc["video_url"] == f"/static/rendered/scene_{i}.mp4"
        assert sc["status"] == "completed"


def test_render_chained_endpoint_success(client):
    scenes_payload = [
        {
            "scene_number": 1,
            "title": "Scene 1",
            "video_config": {"prompt": "Base establishing shot"},
        },
        {
            "scene_number": 2,
            "title": "Scene 2",
            "video_config": {"prompt": "Extend this video continuously: Character acts"},
        },
    ]

    resp = client.post(
        "/api/scriptwriting/render-chained",
        json={"scenes": scenes_payload, "resolution": "720p", "mock_mode": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["total_scenes"] == 2
    assert len(data["scenes"]) == 2
    assert data["cumulative_duration_seconds"] == 10
    assert data["scenes"][0]["turn_number"] == 1
    assert data["scenes"][0]["interaction_id"] is not None
    assert data["scenes"][0]["video_url"].startswith("/static/rendered/")
    assert data["scenes"][1]["turn_number"] == 2
    assert data["scenes"][1]["interaction_id"] is not None


def test_render_chained_endpoint_empty_scenes_error(client):
    resp = client.post(
        "/api/scriptwriting/render-chained",
        json={"scenes": [], "resolution": "720p"},
    )
    assert resp.status_code == 400


def test_render_chained_storyboard_error_resilience():
    engine = OmniFlashExecutionEngine(mock_mode=True)

    scenes = [
        {"scene_number": 1, "video_config": {"prompt": "Scene 1 ok"}},
        {"scene_number": 2, "video_config": {"prompt": "Scene 2 fail"}},
    ]

    call_count = 0

    def mock_generate_video(config, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Gemini API connection error")
        return GenerationResult(
            interaction_thread_id="turn_1_success",
            video_url="/static/rendered/scene_1.mp4",
            duration_seconds=5,
            status="completed",
        )

    engine.generate_video = mock_generate_video

    with pytest.raises(RuntimeError, match="Gemini API connection error"):
        engine.render_chained_storyboard(scenes)
