"""Tests for mixtrain configuration utilities."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from mixtrain.utils.config import Config, WorkspaceConfig


class TestWorkspaceConfig:
    """Test WorkspaceConfig model."""

    def test_workspace_config_creation(self):
        """Test creating a workspace config."""
        config = WorkspaceConfig(name="test-workspace")
        assert config.name == "test-workspace"
        assert config.active is False

    def test_workspace_config_active(self):
        """Test creating an active workspace config."""
        config = WorkspaceConfig(name="test-workspace", active=True)
        assert config.name == "test-workspace"
        assert config.active is True

    def test_workspace_config_serialization(self):
        """Test workspace config serialization."""
        config = WorkspaceConfig(name="test-workspace", active=True)
        data = config.model_dump()
        assert data == {"name": "test-workspace", "active": True}


class TestConfig:
    """Test Config class."""

    def test_config_singleton(self, temp_config_dir):
        """Test that Config is a singleton."""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_config_initialization_new_file(self, temp_config_dir):
        """Test config initialization with new config file."""
        config = Config()
        assert config.workspaces == []
        assert config.auth_token is None
        assert config._config_file.exists()

    def test_config_initialization_existing_file(self, temp_config_dir):
        """Test config initialization with existing config file."""
        # Create a config file first
        config_data = {
            "auth_token": "test_token",
            "workspaces": [
                {"name": "workspace1", "active": True},
                {"name": "workspace2", "active": False}
            ]
        }
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        config = Config()
        assert config.auth_token == "test_token"
        assert len(config.workspaces) == 2
        assert config.workspaces[0].name == "workspace1"
        assert config.workspaces[0].active is True
        assert config.workspaces[1].name == "workspace2"
        assert config.workspaces[1].active is False

    def test_config_initialization_corrupted_file(self, temp_config_dir):
        """Test config initialization with corrupted config file."""
        # Create a corrupted config file
        config_file = temp_config_dir / "config.json"
        config_file.write_text("invalid json")
        
        config = Config()
        assert config.workspaces == []
        assert config.auth_token is None

    def test_config_save(self, temp_config_dir):
        """Test saving configuration."""
        config = Config()
        config.auth_token = "test_token"
        config.workspaces = [
            WorkspaceConfig(name="workspace1", active=True),
            WorkspaceConfig(name="workspace2", active=False)
        ]
        config._save_config()
        
        # Verify file was saved correctly
        saved_data = json.loads(config._config_file.read_text())
        assert saved_data["auth_token"] == "test_token"
        assert len(saved_data["workspaces"]) == 2
        assert saved_data["workspaces"][0]["name"] == "workspace1"
        assert saved_data["workspaces"][0]["active"] is True

    def test_workspace_name_property(self, temp_config_dir):
        """Test workspace_name property."""
        config = Config()
        config.workspaces = [
            WorkspaceConfig(name="workspace1", active=False),
            WorkspaceConfig(name="workspace2", active=True)
        ]
        
        assert config.workspace_name == "workspace2"

    def test_workspace_name_no_active_workspace(self, temp_config_dir):
        """Test workspace_name property with no active workspace."""
        config = Config()
        config.workspaces = [
            WorkspaceConfig(name="workspace1", active=False),
            WorkspaceConfig(name="workspace2", active=False)
        ]
        
        with pytest.raises(Exception, match="No active workspace"):
            config.workspace_name

    def test_workspace_name_no_workspaces(self, temp_config_dir):
        """Test workspace_name property with no workspaces."""
        config = Config()
        config.workspaces = []
        
        with pytest.raises(Exception, match="No active workspace"):
            config.workspace_name

    def test_platform_url_default(self, temp_config_dir):
        """Test platform_url property with default value."""
        config = Config()
        assert config.platform_url == "https://platform.mixtrain.ai/api/v1"

    def test_platform_url_environment_override(self, temp_config_dir):
        """Test platform_url property with environment override."""
        with patch.dict("os.environ", {"MIXTRAIN_PLATFORM_URL": "http://localhost:8000/api/v1"}):
            config = Config()
            assert config.platform_url == "http://localhost:8000/api/v1"

    def test_get_auth_token(self, temp_config_dir):
        """Test getting auth token."""
        config = Config()
        config.auth_token = "test_token"
        assert config.get_auth_token() == "test_token"

    def test_get_auth_token_none(self, temp_config_dir):
        """Test getting auth token when none is set."""
        config = Config()
        assert config.get_auth_token() is None

    def test_set_auth_token_simple(self, temp_config_dir):
        """Test setting auth token without workspace info."""
        config = Config()
        config.set_auth_token("new_token")
        
        assert config.auth_token == "new_token"
        # Verify it was saved
        saved_data = json.loads(config._config_file.read_text())
        assert saved_data["auth_token"] == "new_token"

    def test_set_auth_token_with_workspace_info(self, temp_config_dir):
        """Test setting auth token with workspace info."""
        config = Config()
        workspace_info = {"name": "new-workspace"}
        config.set_auth_token("new_token", workspace_info)
        
        assert config.auth_token == "new_token"
        assert len(config.workspaces) == 1
        assert config.workspaces[0].name == "new-workspace"
        assert config.workspaces[0].active is True

    def test_set_auth_token_update_existing_workspace(self, temp_config_dir):
        """Test setting auth token and updating existing workspace."""
        config = Config()
        config.workspaces = [
            WorkspaceConfig(name="existing-workspace", active=False),
            WorkspaceConfig(name="other-workspace", active=True)
        ]
        
        workspace_info = {"name": "existing-workspace"}
        config.set_auth_token("new_token", workspace_info)
        
        assert config.auth_token == "new_token"
        # Existing workspace should now be active
        existing_ws = next(w for w in config.workspaces if w.name == "existing-workspace")
        assert existing_ws.active is True
        # Other workspace should be deactivated
        other_ws = next(w for w in config.workspaces if w.name == "other-workspace")
        assert other_ws.active is False

    def test_set_auth_token_missing_workspace_name(self, temp_config_dir):
        """Test setting auth token with workspace info missing name."""
        config = Config()
        workspace_info = {"description": "No name"}
        
        with pytest.raises(Exception, match="Server did not provide workspace name"):
            config.set_auth_token("new_token", workspace_info)

    def test_set_workspace_success(self, temp_config_dir):
        """Test setting active workspace."""
        config = Config()
        config.workspaces = [
            WorkspaceConfig(name="workspace1", active=True),
            WorkspaceConfig(name="workspace2", active=False)
        ]
        
        config.set_workspace("workspace2")
        
        # workspace2 should now be active
        ws1 = next(w for w in config.workspaces if w.name == "workspace1")
        ws2 = next(w for w in config.workspaces if w.name == "workspace2")
        assert ws1.active is False
        assert ws2.active is True

    def test_set_workspace_not_found(self, temp_config_dir):
        """Test setting workspace that doesn't exist."""
        config = Config()
        config.workspaces = [
            WorkspaceConfig(name="workspace1", active=True)
        ]
        
        with pytest.raises(Exception, match="Workspace 'nonexistent' not found"):
            config.set_workspace("nonexistent")

    def test_set_workspace_no_workspaces(self, temp_config_dir):
        """Test setting workspace when no workspaces exist."""
        config = Config()
        config.workspaces = []
        
        with pytest.raises(Exception, match="No workspaces available"):
            config.set_workspace("any-workspace")

    def test_config_repr(self, temp_config_dir):
        """Test config string representation."""
        config = Config()
        config.auth_token = "test_token"
        config.workspaces = [WorkspaceConfig(name="test-workspace")]
        
        repr_str = repr(config)
        assert "Config(" in repr_str
        assert "workspaces=" in repr_str
        assert "auth_token=" in repr_str

    def test_config_file_creation_with_nested_directory(self, temp_config_dir):
        """Test config file creation with nested directory structure."""
        # Remove the config directory to test creation
        config_dir = temp_config_dir
        if config_dir.exists():
            import shutil
            shutil.rmtree(config_dir)
        
        config = Config()
        assert config._config_dir.exists()
        assert config._config_file.exists()

    def test_config_save_error_handling(self, temp_config_dir):
        """Test config save with write error."""
        config = Config()
        
        # Mock the entire _config_file to raise an exception on write_text
        with patch.object(config, '_config_file') as mock_file:
            mock_file.write_text.side_effect = PermissionError("Permission denied")
            
            # Should not raise exception, just log error
            config._save_config()
            mock_file.write_text.assert_called_once()

    def test_multiple_config_instances_share_state(self, temp_config_dir):
        """Test that multiple config instances share the same state."""
        config1 = Config()
        config1.auth_token = "test_token"
        config1.workspaces = [WorkspaceConfig(name="test-workspace", active=True)]
        
        config2 = Config()
        assert config2.auth_token == "test_token"
        assert len(config2.workspaces) == 1
        assert config2.workspaces[0].name == "test-workspace"

    def test_config_persistence_across_instances(self, temp_config_dir):
        """Test that config persists across different instances."""
        # Create and configure first instance
        config1 = Config()
        config1.auth_token = "persistent_token"
        config1.workspaces = [WorkspaceConfig(name="persistent-workspace", active=True)]
        config1._save_config()
        
        # Reset singleton to simulate new process
        Config._instance = None
        
        # Create new instance and verify it loads saved config
        config2 = Config()
        assert config2.auth_token == "persistent_token"
        assert len(config2.workspaces) == 1
        assert config2.workspaces[0].name == "persistent-workspace"
        assert config2.workspaces[0].active is True


class TestGetConfigFunction:
    """Test get_config function."""

    def test_get_config_returns_singleton(self, temp_config_dir):
        """Test that get_config returns the singleton instance."""
        from mixtrain.utils.config import get_config
        
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
        assert isinstance(config1, Config)

    def test_get_config_with_existing_instance(self, temp_config_dir):
        """Test get_config when Config instance already exists."""
        from mixtrain.utils.config import get_config
        
        # Create instance directly
        direct_config = Config()
        direct_config.auth_token = "direct_token"
        
        # Get config through function
        function_config = get_config()
        assert function_config is direct_config
        assert function_config.auth_token == "direct_token"
