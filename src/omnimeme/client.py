"""Gemini Enterprise Agent Platform Client Initializer."""

import os

import agentplatform


def get_platform_client(
    project_id: str | None = None,
    location: str | None = None,
) -> agentplatform.Client:
    """Instantiate agentplatform.Client replacing deprecated vertexai.Client."""
    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "omnimeme-dev")
    region = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return agentplatform.Client(project=project, location=region)
