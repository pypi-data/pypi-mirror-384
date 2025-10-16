"""Pytest configuration and fixtures."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()


@pytest.fixture
def test_image_dir() -> Path:
    """Return path to test images directory."""
    return Path(__file__).parent.parent / "tests" / "images"


@pytest.fixture
def sample_image(test_image_dir: Path) -> Path:
    """Return path to a sample test image."""
    # Use the smallest test image
    image_path = test_image_dir / "panther-stadium-statue.jpg"
    if not image_path.exists():
        pytest.skip(f"Test image not found: {image_path}")
    return image_path


@pytest.fixture
def openai_api_key() -> str:
    """Return OpenAI API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set in environment")
    return api_key
    return api_key
