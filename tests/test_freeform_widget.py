from omnimeme.agent import create_omni_director_agent
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request


def test_freeform_input_validation():
    inp = FreeformInput(raw_prompt="A tiger walking through snow")
    assert inp.validate() is True


def test_freeform_input_empty_validation():
    inp = FreeformInput(raw_prompt="   ")
    assert inp.validate() is False


def test_process_freeform_request():
    inp = FreeformInput(raw_prompt="Golden retriever playing fetch in a sunlit meadow")
    agent = create_omni_director_agent()
    res = process_freeform_request(inp, agent)
    assert res["status"] == "success"
    assert "Golden retriever" in res["result"]["enhanced_prompt"]


def test_process_freeform_request_empty():
    inp = FreeformInput(raw_prompt="")
    agent = create_omni_director_agent()
    res = process_freeform_request(inp, agent)
    assert res["status"] == "error"
    assert res["error_message"] == "Prompt cannot be empty."


def test_freeform_input_with_media_attachments():
    from omnimeme.ui.guided_experience import MediaAttachment

    img = MediaAttachment(
        uri="gs://bucket/concept.png", mime_type="image/png", description="Concept Art"
    )
    inp = FreeformInput(
        raw_prompt="Cyberpunk drone flight",
        reference_images=[img],
    )
    agent = create_omni_director_agent()
    res = process_freeform_request(inp, agent)
    assert res["status"] == "success"
    ref_assets = res["result"]["video_config"]["reference_assets"]
    assert len(ref_assets) == 1
    assert ref_assets[0]["uri"] == "gs://bucket/concept.png"
    assert ref_assets[0]["mime_type"] == "image/png"
