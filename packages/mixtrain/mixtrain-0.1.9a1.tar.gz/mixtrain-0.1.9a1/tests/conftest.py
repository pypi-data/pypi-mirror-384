"""Pytest configuration and fixtures for mixtrain tests."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch
from mixtrain.utils.config import Config, WorkspaceConfig


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files during testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch.object(Config, '_config_dir', temp_path):
            with patch.object(Config, '_config_file', temp_path / "config.json"):
                # Reset the singleton instance to use the new path
                Config._instance = None
                yield temp_path


@pytest.fixture
def mock_config(temp_config_dir):
    """Create a mock config with test workspace and auth token."""
    config = Config()
    config.auth_token = "test_auth_token_12345"
    config.workspaces = [
        WorkspaceConfig(name="test-workspace", active=True),
        WorkspaceConfig(name="other-workspace", active=False)
    ]
    config._save_config()
    return config


@pytest.fixture
def test_workspace_name():
    """Return the test workspace name."""
    return "test-workspace"


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,name,value\n")
        f.write("1,test1,100\n")
        f.write("2,test2,200\n")
        f.write("3,test3,300\n")
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def sample_parquet_file():
    """Create a sample Parquet file for testing."""
    import pandas as pd
    
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['test1', 'test2', 'test3'],
        'value': [100, 200, 300]
    })
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        df.to_parquet(f.name)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_platform_url():
    """Mock platform URL for testing."""
    test_url = "http://localhost:8000/api/v1"
    with patch.dict(os.environ, {"MIXTRAIN_PLATFORM_URL": test_url}):
        yield test_url


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    test_key = "mix-test-api-key-12345"
    with patch.dict(os.environ, {"MIXTRAIN_API_KEY": test_key}):
        yield test_key


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset the Config singleton after each test."""
    yield
    Config._instance = None


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing CLI commands."""
    from typer.testing import CliRunner
    return CliRunner()
