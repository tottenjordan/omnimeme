"""Tests for FastAPI server endpoints."""

from fastapi.testclient import TestClient

from omnimeme.server.app import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_enhance_guided_endpoint_success():
    payload = {
        "subject": "Cyberpunk runner",
        "action": "Sprinting in neon rain",
        "camera": "Low angle tracking shot",
        "duration_sec": 7,
        "aspect_ratio": "16:9",
    }
    response = client.post("/api/guided/enhance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Cyberpunk runner" in data["result"]["enhanced_prompt"]
    assert data["result"]["video_config"]["parameters"]["duration_seconds"] == 7


def test_enhance_guided_endpoint_error():
    payload = {"subject": "   "}
    response = client.post("/api/guided/enhance", json=payload)
    assert response.status_code == 400


def test_enhance_freeform_endpoint_success():
    payload = {"raw_prompt": "Golden retriever playing in sunset meadow"}
    response = client.post("/api/freeform/enhance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Golden retriever" in data["result"]["enhanced_prompt"]


def test_enhance_freeform_endpoint_error():
    payload = {"raw_prompt": ""}
    response = client.post("/api/freeform/enhance", json=payload)
    assert response.status_code == 400


def test_stream_guided_endpoint():
    payload = {
        "subject": "Samurai in cherry blossoms",
        "duration_sec": 5,
        "aspect_ratio": "16:9",
    }
    with client.stream("POST", "/api/guided/stream", json=payload) as response:
        assert response.status_code == 200
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("x-accel-buffering") == "no"
        content = "".join(list(response.iter_text()))
        assert "data:" in content
        assert "samurai" in content.lower() or "subject" in content.lower()
        assert '"type": "done"' in content or '"type":"done"' in content


def test_stream_freeform_endpoint():
    payload = {"raw_prompt": "Drone flying through fog"}
    with client.stream("POST", "/api/freeform/stream", json=payload) as response:
        assert response.status_code == 200
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("x-accel-buffering") == "no"
        content = "".join(list(response.iter_text()))
        assert "data:" in content
        assert "drone" in content.lower() or "subject" in content.lower()
        assert '"type": "done"' in content or '"type":"done"' in content


def test_vault_character_crud_and_turnaround_endpoints():
    char_payload = {
        "role_id": "char_test_01",
        "name": "Test Ninja",
        "description": "Stealthy ninja in dark gi",
        "aesthetic_tags": ["anime"],
    }
    # Create character
    resp = client.post("/api/vault/characters", json=char_payload)
    assert resp.status_code == 200
    assert resp.json()["role_id"] == "char_test_01"

    # List characters
    resp = client.get("/api/vault/characters")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 1-Click Turnaround Generation Endpoint
    resp = client.post("/api/vault/characters/char_test_01/turnaround")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert "4-panel view" in resp.json()["turnaround_config"]["prompt"]

    # Delete character
    resp = client.delete("/api/vault/characters/char_test_01")
    assert resp.status_code == 200


def test_gcs_proxy_and_turnaround_with_reference_image():
    # Test GCS proxy endpoint with gs:// URI
    resp = client.get("/api/gcs/proxy?uri=gs://bucket/photo.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ["image/svg+xml", "image/png"]

    # Test GCS proxy endpoint with http(s):// URI (Redirect)
    resp_http = client.get(
        "/api/gcs/proxy?uri=https://example.com/photo.jpg", follow_redirects=False
    )
    assert resp_http.status_code == 307
    assert resp_http.headers["location"] == "https://example.com/photo.jpg"

    # Test Turnaround generation with custom reference_image_url
    char_payload = {
        "role_id": "char_ref_01",
        "name": "Ref Ninja",
        "description": "Ninja with reference photo",
    }
    client.post("/api/vault/characters", json=char_payload)

    resp = client.post(
        "/api/vault/characters/char_ref_01/turnaround",
        json={"reference_image_url": "gs://bucket/ref_ninja.png"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert "gs://bucket/ref_ninja.png" in resp.json()["turnaround_config"]["prompt"]


def test_video_execution_endpoints_and_static_files():
    config_payload = {
        "video_config": {
            "model": "gemini-omni-1.1-flash-preview",
            "prompt": "Cyberpunk runner in neon rain",
            "parameters": {"duration_seconds": 3, "aspect_ratio": "16:9", "resolution": "720p"},
        }
    }
    # Test POST /api/generate-video
    resp = client.post("/api/generate-video", json=config_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["video_url"].startswith("/static/rendered/")

    # Test POST /api/generate-video/stream (SSE streaming)
    stream_resp = client.post("/api/generate-video/stream", json=config_payload)
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    assert "data:" in stream_resp.text
    assert "completed" in stream_resp.text

    # Test static file mounting
    static_url = resp.json()["video_url"]
    static_resp = client.get(static_url)
    assert static_resp.status_code in [200, 206]


def test_user_feedback_endpoint():
    feedback_payload = {
        "interaction_thread_id": "turn_test_123",
        "rating": 5,
        "feedback_type": "prompt_quality",
        "comment": "Outstanding camera motion and lighting expansion!",
        "prompt": "Cyberpunk samurai under neon rain",
    }
    resp = client.post("/api/feedback", json=feedback_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Test invalid rating
    bad_resp = client.post("/api/feedback", json={**feedback_payload, "rating": 6})
    assert bad_resp.status_code == 400

