from omnimeme.agent import create_omni_director_agent
from omnimeme.ui.guided_experience import GuidedPromptInput, process_guided_request


def test_guided_prompt_input_formatting():
    inp = GuidedPromptInput(
        subject="A futuristic cyberpunk runner",
        action="Sprinting across neon puddles",
        camera="Low-angle tracking shot",
        lighting="Rainy night with pink neon reflections",
        style="Cyberpunk thriller 35mm",
        audio="Synthesizer beat and splashing footsteps",
        duration_sec=6,
        aspect_ratio="16:9",
    )
    formatted = inp.to_raw_directive()
    assert "cyberpunk runner" in formatted
    assert "neon puddles" in formatted


def test_process_guided_request():
    inp = GuidedPromptInput(
        subject="Astronaut floating near Saturn",
        action="Reaching towards ring particles",
        camera="Wide orbital push-in",
        duration_sec=8,
        aspect_ratio="9:16",
    )
    agent = create_omni_director_agent()
    res = process_guided_request(inp, agent)
    assert res["status"] == "success"
    assert "Astronaut floating" in res["result"]["enhanced_prompt"]
    assert res["result"]["video_config"]["parameters"]["duration_seconds"] == 8
    assert res["result"]["video_config"]["parameters"]["aspect_ratio"] == "9:16"


def test_guided_prompt_input_validation():
    inp = GuidedPromptInput(subject="   ")
    assert inp.validate() is False
    agent = create_omni_director_agent()
    res = process_guided_request(inp, agent)
    assert res["status"] == "error"
    assert res["error_message"] == "Subject cannot be empty."


def test_guided_prompt_input_with_media_attachments():
    from omnimeme.ui.guided_experience import MediaAttachment

    img = MediaAttachment(
        uri="gs://bucket/style.jpg", mime_type="image/jpeg", description="Style Ref"
    )
    vid = MediaAttachment(
        uri="gs://bucket/action.mp4", mime_type="video/mp4", description="Motion Ref"
    )

    inp = GuidedPromptInput(
        subject="Cyberpunk Samurai",
        reference_images=[img],
        reference_videos=[vid],
    )
    formatted = inp.to_raw_directive()
    assert "Style Ref (gs://bucket/style.jpg)" in formatted
    assert "Motion Ref (gs://bucket/action.mp4)" in formatted

    agent = create_omni_director_agent()
    res = process_guided_request(inp, agent)
    assert res["status"] == "success"
    ref_assets = res["result"]["video_config"]["reference_assets"]
    assert len(ref_assets) == 2
    assert ref_assets[0]["uri"] == "gs://bucket/style.jpg"
    assert ref_assets[1]["uri"] == "gs://bucket/action.mp4"
