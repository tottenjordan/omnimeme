"""Unit tests for GA model migration, SDK payload engine, and structured native audio directing."""

from unittest.mock import MagicMock, patch

from omnimeme.agent import OmniDirectorAgent
from omnimeme.engine import OmniFlashExecutionEngine
from omnimeme.server.app import GuidedApiRequest, omni_director_adk_agent
from omnimeme.tools import enhance_video_prompt, generate_video_config
from omnimeme.ui.guided_experience import GuidedPromptInput


def test_ga_model_defaults():
    agent = OmniDirectorAgent()
    assert agent.model == "gemini-omni-1.1-flash"

    engine = OmniFlashExecutionEngine()
    assert engine.model == "gemini-omni-1.1-flash"

    cfg = generate_video_config("test prompt")
    assert cfg["model"] == "gemini-omni-1.1-flash"

    assert omni_director_adk_agent.model == "gemini-omni-1.1-flash"


def test_structured_native_audio_directing_defaults():
    res = enhance_video_prompt("A superhero flying")
    enhanced = res["enhanced_prompt"]
    assert "[Dialogue]: No dialogue" in enhanced
    assert "[Sound Design]: Subtle ambient sound" in enhanced
    assert "[Music Score]: No background music" in enhanced


def test_structured_native_audio_directing_custom():
    res = enhance_video_prompt(
        "A superhero flying",
        dialogue_text="I will save this city!",
        sound_effects="Wind roaring and sonic boom",
        music_score="Epic orchestral theme",
    )
    enhanced = res["enhanced_prompt"]
    assert "[Dialogue]: I will save this city!" in enhanced
    assert "[Sound Design]: Wind roaring and sonic boom" in enhanced
    assert "[Music Score]: Epic orchestral theme" in enhanced


def test_structured_native_audio_directing_suppression():
    res = enhance_video_prompt(
        "A superhero flying",
        dialogue_text="Ignored text",
        sound_effects="Footsteps",
        music_score="Upbeat pop",
        mute_dialogue=True,
        no_music=True,
    )
    enhanced = res["enhanced_prompt"]
    assert "[Dialogue]: No dialogue" in enhanced
    assert "[Sound Design]: Footsteps" in enhanced
    assert "[Music Score]: No background music" in enhanced


def test_guided_input_and_api_request():
    inp = GuidedPromptInput(
        subject="Hero",
        dialogue_text="Let's go!",
        sound_effects="Laser sound",
        music_score="Synthwave",
        mute_dialogue=False,
        no_music=False,
    )
    directive = inp.to_raw_directive()
    assert "Dialogue: Let's go!" in directive
    assert "Sound Effects: Laser sound" in directive
    assert "Music Score: Synthwave" in directive

    req = GuidedApiRequest(
        subject="Hero",
        dialogue_text="Let's go!",
        sound_effects="Laser sound",
        music_score="Synthwave",
        mute_dialogue=False,
        no_music=False,
    )
    assert req.dialogue_text == "Let's go!"
    assert req.sound_effects == "Laser sound"
    assert req.music_score == "Synthwave"


def test_sdk_payload_fix_engine():
    engine = OmniFlashExecutionEngine(mock_mode=False)
    config = {
        "model": "gemini-omni-1.1-flash",
        "prompt": "Test animation prompt",
        "resolution": "720p",
        "first_frame_uri": "gs://bucket/frame1.png",
        "last_frame_uri": "gs://bucket/frame2.png",
    }

    mock_client = MagicMock()
    mock_interaction = MagicMock()
    mock_interaction.id = "turn_12345"
    mock_client.interactions.create.return_value = mock_interaction

    with patch("google.genai.Client", return_value=mock_client):
        result = engine.generate_video(config)

        mock_client.interactions.create.assert_called_once()
        _, kwargs = mock_client.interactions.create.call_args

        # Ensure model is GA model string
        assert kwargs["model"] == "gemini-omni-1.1-flash"

        # Ensure top-level kwargs do NOT contain first_frame_uri, last_frame_uri, resolution
        assert "first_frame_uri" not in kwargs
        assert "last_frame_uri" not in kwargs
        assert "resolution" not in kwargs

        # Ensure inputs list contains text prompt and image keyframes with correct roles
        inputs = kwargs["input"]
        assert len(inputs) == 3
        assert inputs[0] == {"type": "text", "text": "Test animation prompt"}
        assert inputs[1] == {"type": "image", "gcs_uri": "gs://bucket/frame1.png", "role": "first_frame"}
        assert inputs[2] == {"type": "image", "gcs_uri": "gs://bucket/frame2.png", "role": "last_frame"}

        # Ensure video_config contains resolution
        assert kwargs["video_config"] == {"resolution": "720p"}
