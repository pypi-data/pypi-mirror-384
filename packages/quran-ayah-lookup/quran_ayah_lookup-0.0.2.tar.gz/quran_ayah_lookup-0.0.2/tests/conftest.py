"""
Test configuration for pytest
"""
import pytest
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "بسم الله الرحمن الرحيم"


@pytest.fixture
def sample_surah_ayah():
    """Sample surah and ayah numbers for testing."""
    return {"surah": 1, "ayah": 1}