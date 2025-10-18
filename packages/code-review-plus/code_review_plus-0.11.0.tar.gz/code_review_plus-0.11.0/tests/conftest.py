from pathlib import Path

import pytest

from tests.utils import load_environment_variables


@pytest.fixture
def fixtures_folder() -> Path:
    """Return the path to the fixtures folder."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def requirements_folder() -> Path:
    """Return the path to the requirement_folders folder."""
    return Path(__file__).parent / "fixtures" / "requirements"


@pytest.fixture
def load_environment_vars():
    """Load environment variables for testing."""
    load_environment_variables("local.txt")
