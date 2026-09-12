from omnimeme.config import get_gcp_project, get_gcp_region


def test_get_gcp_project_env_override(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT", "test-project-123")
    assert get_gcp_project() == "test-project-123"


def test_get_gcp_region_default(monkeypatch):
    monkeypatch.delenv("GCP_REGION", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    assert get_gcp_region() == "us-central1"
