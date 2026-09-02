"""Tests for Scriptwriter & Storyboarder Agent and Server API endpoints."""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from omnimeme.agent import OmniDirectorAgent
from omnimeme.scriptwriter import ScriptwriterAgent, create_scriptwriter_agent
from omnimeme.server.app import app
from omnimeme.vault import CharacterRole, CharacterVault


def test_scriptwriter_agent_initialization():
    agent = ScriptwriterAgent()
    assert agent.name == "scriptwriter_agent"
    assert agent.model == "gemini-2.5-flash"
    assert isinstance(agent.director_agent, OmniDirectorAgent)

    # Test factory function
    agent_factory = create_scriptwriter_agent()
    assert agent_factory.model == "gemini-2.5-flash"


def test_generate_storyboard_success():
    agent = ScriptwriterAgent()
    concept = "A futuristic samurai patrolling Neo-Tokyo in heavy rain"
    res = agent.generate_storyboard(
        concept=concept,
        scene_count=3,
        style_preference="Cyberpunk film noir 4K",
    )

    assert res["concept"] == concept
    assert res["scene_count"] == 3
    assert res["style_preference"] == "Cyberpunk film noir 4K"
    assert len(res["scenes"]) == 3

    for i, scene in enumerate(res["scenes"], start=1):
        assert scene["scene_number"] == i
        assert "title" in scene
        assert "visual_description" in scene
        assert "camera_instruction" in scene
        assert "audio_cue" in scene
        assert "video_config" in scene
        assert scene["video_config"]["model"] == "gemini-omni-1.1-flash"
        assert scene["video_config"]["parameters"]["duration_seconds"] == 5


def test_generate_storyboard_with_gemini_api_mock(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_test_key")
    mock_response_json = json.dumps(
        [
            {
                "scene_number": 1,
                "title": "Scene 1: Discovery",
                "visual_description": "Explorer steps into glowing crystal cave.",
                "camera_instruction": "Wide 24mm tracking push-in shot.",
                "audio_cue": "Low crystal resonance frequency sound.",
            },
            {
                "scene_number": 2,
                "title": "Scene 2: Revelation",
                "visual_description": "Ancient alien monolith activates with intense light.",
                "camera_instruction": "Low angle 360 degree orbital rotation.",
                "audio_cue": "Surge of cosmic energy humming loudly.",
            },
        ]
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text=mock_response_json)

    with patch("google.genai.Client", return_value=mock_client):
        agent = ScriptwriterAgent(model="gemini-2.5-flash")
        res = agent.generate_storyboard(
            concept="Space explorer discovers glowing crystal cave monolith",
            scene_count=2,
            style_preference="Cinematic Sci-Fi",
        )

    assert res["scene_count"] == 2
    assert res["scenes"][0]["title"] == "Scene 1: Discovery"
    assert res["scenes"][1]["title"] == "Scene 2: Revelation"
    assert res["scenes"][0]["visual_description"] == "Explorer steps into glowing crystal cave."


def test_generate_storyboard_invalid_concept():
    agent = ScriptwriterAgent()
    with pytest.raises(ValueError, match="Concept cannot be empty"):
        agent.generate_storyboard(concept="   ")


def test_generate_storyboard_with_character_vault():
    vault = CharacterVault()
    char = CharacterRole(
        role_id="kaito_test",
        name="Kaito",
        description="Cyber samurai with blue optic eye",
        turnaround_sheet_url="gs://omnimeme/kaito.png",
    )
    vault.add_character(char)

    agent = ScriptwriterAgent()
    res = agent.generate_storyboard(
        concept="Kaito preparing for battle",
        scene_count=2,
        character_role_id="kaito_test",
        character_vault=vault,
    )

    assert res["character_role_id"] == "kaito_test"
    assert len(res["scenes"]) == 2
    # Verify turnaround reference asset was included in video_config
    first_scene_config = res["scenes"][0]["video_config"]
    assert "reference_assets" in first_scene_config
    assert first_scene_config["reference_assets"][0]["uri"] == "gs://omnimeme/kaito.png"


def test_scriptwriter_agent_remote_a2a_delegation():
    mock_director = MagicMock()
    mock_director.run.return_value = {
        "video_config": {
            "model": "gemini-omni-1.1-flash",
            "prompt": "Federated A2A Director Prompt",
            "parameters": {"duration_seconds": 5},
        }
    }

    agent = ScriptwriterAgent(director_agent=mock_director)
    res = agent.generate_storyboard(
        concept="A dragon flying over snow covered mountains",
        scene_count=1,
    )

    assert len(res["scenes"]) == 1
    assert res["scenes"][0]["video_config"]["prompt"] == "Federated A2A Director Prompt"
    mock_director.run.assert_called_once()


def test_scriptwriting_api_endpoint_success():
    client = TestClient(app)
    payload = {
        "concept": "Space explorer discovering an alien ruin",
        "scene_count": 3,
        "style_preference": "Sci-Fi cinematic IMAX",
    }
    resp = client.post("/api/scriptwriting/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    storyboard = data["storyboard"]
    assert storyboard["concept"] == payload["concept"]
    assert len(storyboard["scenes"]) == 3
    assert storyboard["scenes"][0]["scene_number"] == 1


def test_scriptwriting_api_endpoint_error():
    client = TestClient(app)
    payload = {"concept": "  "}
    resp = client.post("/api/scriptwriting/generate", json=payload)
    assert resp.status_code == 400


def test_a2a_agent_card_endpoint_mounted():
    with TestClient(app) as client:
        resp = client.get("/a2a/app/.well-known/agent-card.json")
        assert resp.status_code == 200
        card = resp.json()
        assert card["name"] == "omni_director"
