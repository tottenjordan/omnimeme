"""Gemini Enterprise Agent Platform Client Initializer."""

import agentplatform

from omnimeme.config import get_gcp_project, get_gcp_region


def get_platform_client(
    project_id: str | None = None,
    location: str | None = None,
) -> agentplatform.Client:
    """Instantiate agentplatform.Client replacing deprecated vertexai.Client."""
    project = project_id or get_gcp_project() or "your-gcp-project-id"
    region = location or get_gcp_region()
    return agentplatform.Client(project=project, location=region)
