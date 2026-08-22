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
