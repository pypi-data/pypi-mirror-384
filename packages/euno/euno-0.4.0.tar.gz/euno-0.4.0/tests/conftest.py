"""
Test configuration and fixtures for the Euno SDK test suite.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "name": "Euno",
        "version": "0.1.0",
    }
