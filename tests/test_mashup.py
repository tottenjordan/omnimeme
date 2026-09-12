"""Tests for Parody & Mashup Video Studio engine, vault bundles, FFmpeg overlays, and FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from omnimeme.engine import concatenate_storyboard_videos
from omnimeme.scriptwriter import ScriptwriterAgent
from omnimeme.server.app import app
from omnimeme.vault import MASHUP_PRESET_BUNDLES


@pytest.fixture
def client():
    return TestClient(app)


def test_vault_mashup_preset_bundles():
    assert isinstance(MASHUP_PRESET_BUNDLES, list)
    assert len(MASHUP_PRESET_BUNDLES) >= 3

    for bundle in MASHUP_PRESET_BUNDLES:
        assert "id" in bundle
        assert "title" in bundle
        assert "character_a" in bundle
        assert "character_b" in bundle
        assert "mashup_genre" in bundle
        assert "parody_tone" in bundle
        assert "role_id" in bundle["character_a"]
        assert "role_id" in bundle["character_b"]


def test_generate_mashup_storyboard_success():
    agent = ScriptwriterAgent()
    res = agent.generate_mashup_storyboard(
        character_a_id="space_lord",
        character_b_id="chef_supreme",
        mashup_genre="Sci-Fi Reality Cooking Show",
        parody_tone="Absurdist Satire",
        product_name="Lightsaber Blender 9000",
        product_description="Plasma-powered countertop blender",
        product_image_url="gs://omnimeme-assets/products/lightsaber_blender.png",
        product_tagline="Puree with the Force!",
        scene_count=4,
    )

    assert res["mashup_genre"] == "Sci-Fi Reality Cooking Show"
    assert res["parody_tone"] == "Absurdist Satire"
    assert res["character_a_id"] == "space_lord"
    assert res["character_b_id"] == "chef_supreme"
    assert res["scene_count"] == 4
    assert len(res["scenes"]) == 4

    assert res["product"]["name"] == "Lightsaber Blender 9000"
    assert res["product"]["tagline"] == "Puree with the Force!"

    # Check lower third titles & alternating beats
    scene1 = res["scenes"][0]
    scene2 = res["scenes"][1]
    scene3 = res["scenes"][2]
    scene4 = res["scenes"][3]

    assert "lower_third_title" in scene1
    assert "lower_third_title" in scene2
    assert "lower_third_title" in scene3
    assert "lower_third_title" in scene4

    # Commercial beat product reference asset check
    ref_assets = scene3["video_config"].get("reference_assets", [])
    assert any("Lightsaber Blender" in asset.get("description", "") for asset in ref_assets)


def test_generate_mashup_storyboard_validation():
    agent = ScriptwriterAgent()
    with pytest.raises(ValueError, match="character_a_id and character_b_id are required"):
        agent.generate_mashup_storyboard(character_a_id="", character_b_id="chef_supreme")


def test_concatenate_storyboard_videos_with_overlays(tmp_path):
    video_urls = ["/static/rendered/test_clip_1.mp4", "/static/rendered/test_clip_2.mp4"]
    lower_third_titles = [
        {"name": "Space Lord", "role": "Galactic Tyrant"},
        {"name": "Chef Supreme", "role": "Master Chef"},
    ]
    product_sponsor_callout = "Lightsaber Blender 9000 - Puree with the Force!"

    master_url = concatenate_storyboard_videos(
        video_urls=video_urls,
        output_filename="test_mashup_master.mp4",
        lower_third_titles=lower_third_titles,
        product_sponsor_callout=product_sponsor_callout,
    )

    assert master_url.startswith("/static/rendered/")
    assert "test_mashup_master.mp4" in master_url


def test_api_get_mashup_bundles(client):
    response = client.get("/api/vault/mashup-bundles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert data[0]["id"] == "space_lord_vs_chef"


def test_api_post_mashup_storyboard(client):
    payload = {
        "character_a_id": "cyberpunk_ronin",
        "character_b_id": "film_noir_detective",
        "mashup_genre": "Neon Cyber-Noir",
        "parody_tone": "Hard-Boiled Parody",
        "product": {
            "name": "Cyber-Fedora Neural HUD",
            "description": "Classic fedora with 8K HUD",
            "image_url": "gs://omnimeme-assets/products/cyber_fedora.png",
            "tagline": "Solve crimes in style.",
        },
        "scene_count": 4,
    }
    response = client.post("/api/scriptwriting/mashup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "storyboard" in data
    storyboard = data["storyboard"]
    assert storyboard["character_a_id"] == "cyberpunk_ronin"
    assert len(storyboard["scenes"]) == 4


def test_api_post_mashup_storyboard_validation(client):
    payload = {
        "character_a_id": "",
        "character_b_id": "film_noir_detective",
    }
    response = client.post("/api/scriptwriting/mashup", json=payload)
    assert response.status_code == 400


def test_guided_and_freeform_api_requests_with_character_b_and_product(client):
    guided_payload = {
        "subject": "Cyber Ronin vs Noir Detective in rainy Neo-Chicago",
        "character_role_id": "cyberpunk_ronin",
        "character_b_role_id": "film_noir_detective",
        "product": {
            "name": "Cyber-Fedora",
            "tagline": "Style & tech combined",
        },
    }
    response_guided = client.post("/api/guided/enhance", json=guided_payload)
    assert response_guided.status_code == 200

    freeform_payload = {
        "raw_prompt": "Space Lord selling Lightsaber Blender in infomercial",
        "character_role_id": "space_lord",
        "character_b_role_id": "chef_supreme",
        "product": {
            "name": "Lightsaber Blender 9000",
        },
    }
    response_freeform = client.post("/api/freeform/enhance", json=freeform_payload)
    assert response_freeform.status_code == 200


def test_concatenate_storyboard_videos_string_and_special_char_overlays(tmp_path):
    video_urls = ["/static/rendered/test_clip_1.mp4"]
    lower_third_titles = ["Space Lord - Galactic Tyrant"]
    product_sponsor_callout = "Lightsaber Blender\\ 9000 (100% Force! & 50% Off: Special)"

    master_url = concatenate_storyboard_videos(
        video_urls=video_urls,
        output_filename="test_special_chars_master.mp4",
        lower_third_titles=lower_third_titles,
        product_sponsor_callout=product_sponsor_callout,
    )
    assert master_url.startswith("/static/rendered/")
    assert "test_special_chars_master.mp4" in master_url


def test_generate_mashup_storyboard_whitespace_validation():
    agent = ScriptwriterAgent()
    with pytest.raises(ValueError, match="character_a_id and character_b_id are required"):
        agent.generate_mashup_storyboard(character_a_id="   ", character_b_id="chef_supreme")
