from omnimeme.agent import create_omni_director_agent
from omnimeme.tools import enhance_video_prompt, generate_video_config


def test_enhance_video_prompt_tool():
    res = enhance_video_prompt(
        raw_prompt="A car driving down the street",
        director_notes="Make it dramatic rain at night",
    )
    assert "[Subject]:" in res["enhanced_prompt"]
    assert "[Lighting & Atmosphere]:" in res["enhanced_prompt"]
    assert "rain" in res["enhanced_prompt"].lower() or "dramatic" in res["enhanced_prompt"].lower()


def test_generate_video_config_tool():
    cfg = generate_video_config(
        enhanced_prompt="Cinematic shot of a car in rain",
        duration_sec=5,
        aspect_ratio="16:9",
    )
    assert cfg["model"] == "gemini-omni-flash-preview"
    assert cfg["parameters"]["duration_seconds"] == 5
    assert cfg["parameters"]["aspect_ratio"] == "16:9"


def test_omni_director_agent_creation():
    agent = create_omni_director_agent()
    assert agent.name == "omni_director"
