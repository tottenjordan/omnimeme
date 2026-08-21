"""Tests for agentplatform.Client initializer."""

from omnimeme.client import get_platform_client


def test_get_platform_client_defaults():
    client = get_platform_client()
    assert client is not None


def test_get_platform_client_custom_params():
    client = get_platform_client(project_id="my-custom-proj", location="us-central1")
    assert client is not None
