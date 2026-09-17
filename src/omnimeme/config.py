"""Central Configuration & Dynamic Environment Loader for OmniMeme."""

import os
import subprocess

from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()


def get_gcp_project() -> str:
    """Dynamically resolves the active GCP project ID from .env, env vars, or gcloud CLI."""
    project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if project:
        return project.strip()
    try:
        res = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True,
        )
        out = res.stdout.strip()
        if out and not out.startswith("("):
            return out
    except Exception:
        pass
    return ""


def get_gcp_region() -> str:
    """Dynamically resolves the active GCP region from .env or env vars."""
    return os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"
