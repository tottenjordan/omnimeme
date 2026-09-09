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
        resolution="1080p",
        first_frame_uri="gs://bucket/start.png",
        last_frame_uri="gs://bucket/end.png",
    )
    assert cfg["model"] == "gemini-omni-1.1-flash"
    assert cfg["parameters"]["duration_seconds"] == 5
    assert cfg["parameters"]["aspect_ratio"] == "16:9"
    assert cfg["parameters"]["resolution"] == "1080p"
    assert cfg["parameters"]["first_frame_uri"] == "gs://bucket/start.png"
    assert cfg["parameters"]["last_frame_uri"] == "gs://bucket/end.png"


def test_omni_director_agent_creation():
    agent = create_omni_director_agent()
    assert agent.name == "omni_director"
    assert agent.model == "gemini-omni-1.1-flash"


def test_generate_video_config_tool_with_reference_assets():
    assets = [
        {"uri": "gs://bucket/frame.png", "mime_type": "image/png", "description": "Keyframe"},
        {"uri": "gs://bucket/motion.mp4", "mime_type": "video/mp4", "description": "Camera Motion"},
    ]
    cfg = generate_video_config(
        enhanced_prompt="Cinematic drone flight",
        duration_sec=7,
        aspect_ratio="16:9",
        reference_assets=assets,
    )
    assert cfg["reference_assets"] == assets
    assert len(cfg["reference_assets"]) == 2


def test_enhance_video_prompt_with_character_role():
    from omnimeme.vault import CharacterRole

    char = CharacterRole(
        role_id="char_samurai_01",
        name="Cyber Samurai",
        description="Obsidian armor samurai",
        turnaround_sheet_url="gs://bucket/samurai_turnaround.png",
    )
    res = enhance_video_prompt(
        raw_prompt="Samurai walking in rain",
        character_role=char,
    )
    assert "@Image1: Character Reference - Cyber Samurai" in res["enhanced_prompt"]
    assert "Obsidian armor samurai" in res["enhanced_prompt"]


def test_omni_director_agent_run_with_character_role():
    from omnimeme.vault import CharacterRole

    char = CharacterRole(
        role_id="char_samurai_01",
        name="Cyber Samurai",
        description="Obsidian armor samurai",
        turnaround_sheet_url="gs://bucket/samurai_turnaround.png",
    )
    agent = create_omni_director_agent()
    res = agent.run(user_prompt="Samurai walking in rain", character_role=char)

    assert "@Image1: Character Reference - Cyber Samurai" in res["enhanced_prompt"]
    assert "video_config" in res
    assert "reference_assets" in res["video_config"]
    assert res["video_config"]["reference_assets"][0] == {
        "uri": "gs://bucket/samurai_turnaround.png",
        "mime_type": "image/png",
        "description": "Cyber Samurai Turnaround Sheet (@Image1)",
    }
