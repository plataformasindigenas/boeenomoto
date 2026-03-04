"""Shared fixtures for Boe Eno Moto tests."""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def data_dir():
    return PROJECT_ROOT / "data"


@pytest.fixture
def docs_dir():
    return PROJECT_ROOT / "docs"


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory with minimal test data."""
    d = tmp_path / "data"
    d.mkdir()
    return d
