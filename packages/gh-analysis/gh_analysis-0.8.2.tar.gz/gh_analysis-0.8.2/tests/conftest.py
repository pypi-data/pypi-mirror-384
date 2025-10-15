"""Test configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory structure."""
    data_dir = tmp_path / "data"
    (data_dir / "issues").mkdir(parents=True)
    (data_dir / "results").mkdir(parents=True)
    return data_dir
