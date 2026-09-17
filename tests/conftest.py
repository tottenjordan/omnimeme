import glob
import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_rendered_test_artifacts():
    """Autouse fixture to clean up synthetic preview media files in static/rendered/ after test sessions."""
    yield
    rendered_dir = os.path.join(os.path.dirname(__file__), "..", "static", "rendered")
    if os.path.exists(rendered_dir):
        for pattern in ["*.mp4", "*.wav", "*.png", "*.jpg", "*.txt"]:
            for filepath in glob.glob(os.path.join(rendered_dir, pattern)):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
